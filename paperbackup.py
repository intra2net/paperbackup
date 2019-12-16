#!/usr/bin/env python3

#
# create a pdf with barcodes to backup text files on paper
# designed to backup ascii-armored key files and ciphertext
#

# Copyright 2017 by Intra2net AG, Germany
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#

import os
import logging
import re
import sys
import hashlib
import subprocess
import qrencode
import argparse
from tempfile import mkstemp
from datetime import datetime
from PIL import Image
from pyx import *


def create_barcode(chunkdata):
    version, size, im = qrencode.encode(chunkdata,
                                        level=qrencode.QR_ECLEVEL_H,
                                        case_sensitive=True)
    return im


def finish_page(pdf, canv, pageno):
    canv.text(10, 0.6, "Page %i" % (pageno+1))
    pdf.append(document.page(canv, paperformat=paperformat_obj,
                             fittosize=0, centered=0))


# main code

parser = argparse.ArgumentParser(description='Generate a PDF with barcodes for a given file.')
parser.add_argument('-c', dest='columns', nargs=1, default=[4], type=int,
                    help='number of columns per page (default: 4)')
parser.add_argument('-d', dest='debug', action='store_true',
                    help='debug output')
parser.add_argument('-g', dest='gap', nargs=1, default=[2], type=int,
                    help='minimum gap (%%, default: 2)')
parser.add_argument('-r', dest='rows', nargs=1, default=[5], type=int,
                    help='number of rows per page (default: 5)')
parser.add_argument('-s', dest='paper_size', nargs=1, default=['a4'],
                    help='paper size: a4 or letter (default: a4)')
parser.add_argument('input_file', nargs=1,
                    help='file to process (perhaps base64-encoded)')

args = parser.parse_args()

if not args.input_file:
    parser.print_help()
    sys.exit()

input_file = args.input_file[0]

if args.debug:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.CRITICAL)

# constants for the size and layout of the barcodes on page
max_bytes_in_barcode = 140

# page margins
top_margin = 2.2
right_margin = 1.2
left_margin = 1.5
bottom_margin = 1.5

paper_size = args.paper_size[0].lower()

if paper_size == 'a4':
    paperformat_obj = document.paperformat.A4
    paperformat_str = "A4"
    # paper size in cm
    paper_width = 21
    paper_height = 29.7
else:
    paperformat_obj=document.paperformat.Letter
    paperformat_str="Letter"
    # paper size in cm
    paper_width = 21.6
    paper_height = 27.9

logging.info('Paper size: {0}'.format(paper_size))

# number of barcode rows/columns per page (4/5 by default)
barcode_cols = args.columns[0]
barcode_rows = args.rows[0]

cell_width = (paper_width - left_margin - right_margin) / barcode_cols
cell_height = (paper_height - top_margin - bottom_margin) / barcode_rows

# fix "X"
logging.info('Cell dimensions: {0:.2f}×{1:.2f} cm'.format(cell_width, cell_height))

gap_perc = args.gap[0]

if cell_width <= cell_height:
    horizontal_gap = gap_perc * cell_width / 100
    barcode_height = cell_width - horizontal_gap
    vertical_gap = cell_height - barcode_height
else:
    vertical_gap = gap_perc * cell_height / 100
    barcode_height = cell_height - vertical_gap
    horizontal_gap = cell_width - barcode_height

logging.info('Horizontal gap: {0:.2f} cm'.format(horizontal_gap))
logging.info('Vertical gap: {0:.2f} cm'.format(vertical_gap))
logging.info('Barcode height/width: {0:.2f} cm'.format(barcode_height))


barcode_x_positions = [left_margin + (x * (horizontal_gap + barcode_height)) for x in range(barcode_cols)] * barcode_rows
barcode_y_positions = list()
[barcode_y_positions.extend(barcode_cols * [bottom_margin + (x * (vertical_gap + barcode_height))]) for x in range(barcode_rows)]
barcode_y_positions.reverse()
barcodes_per_page = barcode_rows * barcode_cols
text_x_offset = 0
text_y_offset = barcode_height + 0.2
logging.info('Barcode x positions: {0}'.format(barcode_x_positions))
logging.info('Barcode y positions: {0}'.format(barcode_y_positions))

# align to top margin
content_top = max(barcode_y_positions) + text_y_offset
header_content_gap = paper_height - top_margin - content_top
barcode_y_positions = [x + header_content_gap for x in barcode_y_positions]

plaintext_maxlinechars = 73

if not os.path.isfile(input_file):
    raise RuntimeError('File {} not found'.format(input_file))
just_filename = os.path.basename(input_file)

with open(input_file) as inputfile:
    ascdata = inputfile.read()

# only allow some harmless characters
# this is much more strict than neccessary, but good enough for key files
# you really need to forbid ^, NULL and anything that could upset enscript
allowedchars = re.compile(r"^[A-Za-z0-9/=+:., #@!()\n-]*")
allowedmatch = allowedchars.match(ascdata)
if allowedmatch.group() != ascdata:
    raise RuntimeError('Illegal char found at %d >%s<.\n'
                       'Maybe you want to base64-encode the file first?'
                       % (len(allowedmatch.group()),
                          ascdata[len(allowedmatch.group())]))

# split the ascdata into chunks of max_bytes_in_barcode size
# each chunk begins with ^<sequence number><space>
# this allows to easily put them back together in the correct order
barcode_blocks = []
chunkdata = "^1 "
for char in list(ascdata):
    if len(chunkdata)+1 > max_bytes_in_barcode:
        # chunk is full -> create barcode from it
        logging.debug('Creating barcode no {0}'.format(len(barcode_blocks) + 1))
        logging.debug('Chunkdata: {0}'.format(chunkdata))
        barcode_blocks.append(create_barcode(chunkdata))
        chunkdata = "^" + str(len(barcode_blocks)+1) + " "

    chunkdata += char

# handle the last, non filled chunk too
if len(chunkdata) > len(str(len(barcode_blocks))) + 2:
    logging.debug('Creating barcode no {0}'.format(len(barcode_blocks) + 1))
    logging.debug('Chunkdata: {0}'.format(chunkdata))
    barcode_blocks.append(create_barcode(chunkdata))

# init PyX
unit.set(defaultunit="cm")
pdf = document.document()

# place barcodes on pages
pgno = 0   # page number
ppos = 0   # position id on page

if len(just_filename) > 19:
    font_size = text.size.tiny
elif len(just_filename) > 15:
    font_size = text.size.small
elif len(just_filename) > 10:
    font_size = text.size.normal
else:
    font_size = text.size.Large

logging.debug('Font size for QR labels: {0}'.format(font_size.size))

c = canvas.canvas()
for bc in range(len(barcode_blocks)):
    # page full?
    if ppos >= barcodes_per_page:
        finish_page(pdf, c, pgno)
        c = canvas.canvas()
        pgno += 1
        ppos = 0

    c.text(barcode_x_positions[ppos] + text_x_offset,
           barcode_y_positions[ppos] + text_y_offset,
           "%s (%i/%i)" % (text.escapestring(just_filename),
                           bc+1, len(barcode_blocks)),
           [font_size])
    c.insert(bitmap.bitmap(barcode_x_positions[ppos],
                           barcode_y_positions[ppos],
                           barcode_blocks[bc], height=barcode_height))
    ppos += 1

finish_page(pdf, c, pgno)
pgno += 1

fd, temp_barcode_path = mkstemp('.pdf', 'qr_', '.')
# will use pdf as the tmpfile has a .pdf suffix
pdf.writetofile(temp_barcode_path)

# prepare plain text output
fd, temp_text_path = mkstemp('.ps', 'text_', '.')
input_file_modification = datetime.fromtimestamp(os.path.getmtime(input_file)).strftime("%Y-%m-%d %H:%M:%S")

# split lines on plaintext_maxlinechars - ( checksum_size + separator size)
splitat=plaintext_maxlinechars - 8
splitlines=[]
for line in ascdata.splitlines():
    while len(line) > splitat:
        splitlines.append(line[:splitat])
        # add a ^ at the beginning of the broken line to mark the linebreak
        line="^"+line[splitat:]
    splitlines.append(line)

# add checksums to each line
chksumlines=[]
for line in splitlines:
    # remove the linebreak marks for checksumming
    if len(line) > 1 and line[0] == "^":
        sumon=line[1:]
    else:
        sumon=line

    # use the first 6 bytes of MD5 as checksum
    chksum = hashlib.md5(sumon.encode('utf-8')).hexdigest()[:6]

    # add the checksum right-justified to the line
    line+=" "*(splitat-len(line))
    line+=" |"+chksum

    chksumlines.append(line)

# we also want a checksum which the restored file should match
checksum = hashlib.sha256(bytes(ascdata, 'utf8')).hexdigest()

# add some documentation around the plaintest
outlines=[]
coldoc=" "*splitat
coldoc+=" | MD5"
outlines.append(coldoc)
outlines.extend(chksumlines)
outlines.append("")
outlines.append("")
outlines.append("sha256sum of input file:")
outlines.append("%s"%checksum)
outlines.append("")
outlines.append("")
outlines.append("--")
outlines.append("Created with paperbackup.py")
outlines.append("See https://github.com/intra2net/paperbackup/ for instructions")

# use "enscript" to create postscript with the plaintext
p = subprocess.Popen(
        ["enscript", "-p"+temp_text_path, "-f", "Courier12",
            "-t" + just_filename,
            "-M" + paperformat_str, "--header",
            just_filename + "|" + input_file_modification + "|Page $%"],
        stdout=subprocess.PIPE, stdin=subprocess.PIPE)

# send the text to enscript
for line in outlines:
    p.stdin.write(line.encode('utf-8'))
    p.stdin.write(os.linesep.encode('utf-8'))

p.communicate()[0]
p.stdin.close()

if p.returncode != 0:
    raise RuntimeError('error calling enscript')

# combine both files with ghostscript

ret = subprocess.call(["gs", "-dBATCH", "-dNOPAUSE", "-q", "-sDEVICE=pdfwrite",
                       "-sOutputFile=" + just_filename + ".pdf",
                       temp_barcode_path, temp_text_path])
if ret != 0:
    raise RuntimeError('error calling ghostscript')

# using enscript and ghostscript to create the plaintext output is a hack,
# using PyX and LaTeX would be more elegant. But I could not find an easy
# solution to flow the text over several pages with PyX.

os.remove(temp_text_path)
os.remove(temp_barcode_path)

print("Please now verify that the output can be restored by calling:")
print("paperbackup-verify.sh {}.pdf".format(just_filename))

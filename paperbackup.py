#!/usr/bin/python3

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
import re
import sys
import shlex
import qrencode
from tempfile import mkstemp
from PIL import Image
from pyx import *

# constants for the size and layout of the barcodes on page
max_bytes_in_barcode = 140
barcodes_per_page = 6
barcode_height = 8
barcode_x_positions = [1.5, 11, 1.5, 11, 1.5, 11]
barcode_y_positions = [18.7, 18.7, 10, 10, 1.2, 1.2]
text_x_offset = 0
text_y_offset = 8.2

# the paperformat to use, activate the one you want
paperformat_obj = document.paperformat.A4
paperformat_str = "A4"
# paperformat_obj=document.paperformat.Letter
# paperformat_str="Letter"


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

if len(sys.argv) != 2:
    raise RuntimeError('Usage {} FILENAME.asc'.format(sys.argv[0]))

input_path = sys.argv[1]
if not os.path.isfile(input_path):
    raise RuntimeError('File {} not found'.format(input_path))
just_filename = os.path.basename(input_path)

with open(input_path) as inputfile:
    ascdata = inputfile.read()

# only allow some harmless characters
# this is much more strict than neccessary, but good enough for key files
# you really need to forbid ^, NULL and anything that could upset enscript
allowedchars = re.compile(r"^[A-Za-z0-9/=+:., #@!()\n-]*")
allowedmatch = allowedchars.match(ascdata)
if allowedmatch.group() != ascdata:
    raise RuntimeError('Illegal char found at %d >%s<'
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
        barcode_blocks.append(create_barcode(chunkdata))
        chunkdata = "^" + str(len(barcode_blocks)+1) + " "

    chunkdata += char

# handle the last, non filled chunk too
barcode_blocks.append(create_barcode(chunkdata))

# init PyX
unit.set(defaultunit="cm")
pdf = document.document()

# place barcodes on pages
pgno = 0   # page number
ppos = 0   # position id on page
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
                           bc+1, len(barcode_blocks)))
    c.insert(bitmap.bitmap(barcode_x_positions[ppos],
                           barcode_y_positions[ppos],
                           barcode_blocks[bc], height=barcode_height))
    ppos += 1

finish_page(pdf, c, pgno)
pgno += 1

fd, temp_barcode_path = mkstemp('.pdf', 'qr_', '.')
# will use pdf as the tmpfile has a .pdf suffix
pdf.writetofile(temp_barcode_path)

# use "enscript" to create postscript with the plaintext
fd, temp_text_path = mkstemp('.ps', 'text_', '.')
ret = os.system("enscript -p" + shlex.quote(temp_text_path) +
                " -f Courier12 -M" + paperformat_str +
                " " + shlex.quote(input_path))
if ret != 0:
    raise RuntimeError('error calling enscript')

# combine both files with ghostscript
ret = os.system("gs -dBATCH -dNOPAUSE -q -sDEVICE=pdfwrite -sOutputFile=" +
                shlex.quote(just_filename) +
                ".pdf " + shlex.quote(temp_barcode_path) + " " +
                shlex.quote(temp_text_path))
if ret != 0:
    raise RuntimeError('error calling ghostscript')

# using enscript and ghostscript to create the plaintext output is a hack,
# using PyX and LaTeX would be more elegant. But I could not find an easy
# solution to flow the text over several pages with PyX.

os.remove(temp_text_path)
os.remove(temp_barcode_path)

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

########################################################################
# BEGIN OF CUSTOMIZATION SECTION

# The paperformat to use, activate the one you want
paperformat_str = "A4"
#paperformat_str="Letter"

# constants for the size and layout of the barcodes on page
max_bytes_in_barcode = 140
barcodes_per_page = 6

l_unit = "cm"  # or "inch"
barcode_height = 8
barcode_x_positions = [1.5, 11, 1.5, 11, 1.5, 11]
barcode_y_positions = [18.7, 18.7, 10, 10, 1.2, 1.2]
text_x_offset = 0
text_y_offset = 8.2

plaintext_maxlinechars = 73

# END OF CUSTOMIZATION SECTION
########################################################################

import os
import re
import sys
import hashlib
import qrencode
import logging

# TODO: implement argument switch to force usage of pyx
try:
    import reportlab  # to check if we can use it
    from reportlab.pdfgen import canvas
    from reportlab.lib import pagesizes
    from reportlab.lib.utils import ImageReader
    from reportlab.lib.units import cm, inch
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
except ModuleNotFoundError:
    import subprocess
    from tempfile import mkstemp
    from datetime import datetime
    from PIL import Image
    from pyx import *

logging.basicConfig(level=logging.WARN)

if 'reportlab' in sys.modules:
    USE_REPORTLAB = True
else:
    USE_REPORTLAB = False
logging.debug("USE_REPORTLAB is %s"%USE_REPORTLAB)

# tool-specific setup for paper format, positions, etc.
if USE_REPORTLAB:
    if str.isdigit(paperformat_str[-1]):
        # "A4", etc.
        paperformat_obj = getattr(pagesizes, paperformat_str, 'A4')
    else:
        # "Letter", "legal", etc.
        paperformat_obj = getattr(pagesizes, paperformat_str.lower(), 'letter')
    # Bring all measurements into correct units
    l_unit = getattr(reportlab.lib.units, l_unit, 'cm')
    barcode_height = barcode_height * l_unit
    barcode_x_positions = [ x * l_unit for x in barcode_x_positions ]
    barcode_y_positions = [ x * l_unit for x in barcode_y_positions ]
    text_x_offset = text_x_offset * l_unit
    text_y_offset = text_y_offset * l_unit
else:
    # PyX
    paperformat_obj = getattr(document.paperformat, paperformat_str, 'A4')

def create_barcode(chunkdata):
    version, size, im = qrencode.encode(chunkdata,
                                        level=qrencode.QR_ECLEVEL_H,
                                        case_sensitive=True)
    return im


def finish_page(pdf, canv, pageno, USE_REPORTLAB=USE_REPORTLAB, l_unit=l_unit):
    if USE_REPORTLAB:
        canv.drawString(10*l_unit, 0.6*l_unit, "Page %i" % (pageno+1))
    else:
        canv.text(10, 0.6, "Page %i" % (pageno+1))
        pdf.append(document.page(canv, paperformat=paperformat_obj,
                                fittosize=0, centered=0))

def create_chunks(ascdata, max_bytes_in_barcode):
    """Chunk ascdata into a list of blocks with size max_bytes_in_barcode or less.
    Only specific ASCII characters are allowed in ascdata so we don't worry about Unicode.
    Each block begins with ^<sequence number><space> (1-based).
    This allows to easily put them back together in the correct order."""
    # Slicing ascdata reduces processing time to about 5% compared to handling each char separately
    chunks = []
    chunk_idx = 0
    while chunk_idx < len(ascdata):
        chunkdata = "^" + str(len(chunks)+1) + " "
        charnum = max_bytes_in_barcode - len(chunkdata)
        chunks.append(chunkdata + ascdata[chunk_idx:chunk_idx+charnum])
        chunk_idx += charnum
    return chunks

def prepare_plainlines(ascdata, plaintext_maxlinechars):
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

    # add some documentation around the plaintest
    outlines=[]
    coldoc=" "*splitat
    coldoc+="truncated"
    outlines.append(coldoc)
    coldoc=" "*splitat
    coldoc+="   MD5"
    outlines.append(coldoc)
    outlines.extend(chksumlines)
    outlines.append("")
    outlines.append("")
    outlines.append("")
    outlines.append("--")
    outlines.append("Created with paperbackup.py")
    outlines.append("See https://github.com/intra2net/paperbackup/ for instructions")

    outlines.append("")
    outlines.append("             -----------------------------------------")
    outlines.append("")
    outlines.append("The full alphabet and some special characters for comparison:")
    outlines.append("  ABCDEFGHIJKLMNOPQRSTUVWXYZ -- 0123456789 / = + : . , # @ ! ( ) \ n -")
    outlines.append("  abcdefghijklmnopqrstuvwxyz --        ... colon fullstop comma ...")
    # TODO: if argument switch to include restore script:
    outlines.append("")
    outlines.append("             -----------------------------------------")
    outlines.append("")
    outlines.append("Below is a minimal copy of the paperrestore.sh script")
    outlines.append("For a full-fledged restore script please see the above resources.")
    outlines.append("")
    outlines.append("             -----------------------------------------")
    outlines.append("")
    outlines.append("#  [...]")

    outlines.append("# WARNING: do NOT type in the line number markers")
    outlines.append("#           on the far right side! ----------------------------------vvv")
    outlines.append("                                                                               ")
    outlines.append("# zbarimg ends each scanned code with a newline                      #01")
    outlines.append("                                                                     #02")
    outlines.append("# each barcode content begins with ^<number><space>                  #03")
    outlines.append("# so convert that to \\0<number><space>, so sort can sort on that     #04")
    outlines.append("# then remove all \\n\\0<number><space> so we get the originial        #05")
    outlines.append("# without newlines added                                             #06")
    outlines.append("                                                                     #07")
    outlines.append('/usr/bin/zbarimg --raw -Sdisable -Sqrcode.enable "$SCANNEDFILE" \    #08')
    outlines.append('    | sed -e "s/\^/\\x0/g" \                                          #09')
    outlines.append("    | sort -z -n \                                                   #10")
    outlines.append("    | sed ':a;N;$!ba;s/\\n\\x0[0-9]* //g;s/\\x0[0-9]* //g;s/\\n\\x0//g'   #11")
    outlines.append("#position of spaces:              H               H                  #12")
    return outlines

def search_DPCustomMono2_font(USE_REPORTLAB=USE_REPORTLAB):
    # Try really hard to use the DPCustomMono2 font from Distributed Proofreaders
    # see: https://www.pgdp.net/wiki/DP_Official_Documentation:Proofreading/DPCustomMono2_Font
    if not USE_REPORTLAB:
        raise Exception("DONT CALL search_DPCustomMono2_font() WHEN NOT USING REPORTLAB!")
    font_locations = [os.path.join(os.path.dirname(sys.argv[0]), "DPCustomMono2.ttf"),
                      '~/.fonts/DPCustomMono2.ttf',
                      '~/.fonts/DPCustomMono2/DPCustomMono2.ttf',
                      '~/.local/share/fonts/DPCustomMono2.ttf',
                      '~/.local/share/fonts/DPCustomMono2/DPCustomMono2.ttf',
                      '/usr/share/fonts/TTF/DPCustomMono2.ttf',
                      '/usr/share/fonts/truetype/DPCustomMono2.ttf',
                      '/usr/X11R6/lib/X11/fonts/ttfonts/DPCustomMono2.ttf',
                      '/usr/X11R6/lib/X11/fonts/DPCustomMono2.ttf']
    font_name = None
    font_idx = 0
    while font_name is None and font_idx < len(font_locations):
        try:
            pdfmetrics.registerFont(TTFont('DPCustomMono2',
                                        os.path.expanduser(font_locations[font_idx])))
        except reportlab.pdfbase.ttfonts.TTFError:
            font_name = None
            logging.debug("Font NOT found in: %s"%font_locations[font_idx])
        else:
            font_name = "DPCustomMono2"
            logging.debug("Font was FOUND in: %s"%font_locations[font_idx])
        finally:
            font_idx += 1
    return font_name

if __name__ == "__main__":

    if len(sys.argv) != 2:
        raise RuntimeError('Usage {} FILENAME.asc'.format(sys.argv[0]))

    input_path = sys.argv[1]
    if not os.path.isfile(input_path):
        raise RuntimeError('File {} not found'.format(input_path))
    just_filename = os.path.basename(input_path)

    with open(input_path) as inputfile:
        ascdata = inputfile.read()

    # Only allow some harmless characters
    # This is much more strict than neccessary, but good enough for key files
    # you really need to forbid ^, NULL and anything that could upset enscript.
    # This also ensures that we have only single-byte characters, i.e. no Unicode, for chunking
    allowedchars = re.compile(r"^[A-Za-z0-9/=+:., #@!()\n-]*")
    allowedmatch = allowedchars.match(ascdata)
    if allowedmatch.group() != ascdata:
        raise RuntimeError('Illegal char found at %d >%s<'
                           % (len(allowedmatch.group()),
                              ascdata[len(allowedmatch.group())]))

    # split the ascdata into chunks of max_bytes_in_barcode size
    # each chunk begins with ^<sequence number><space>
    # this allows to easily put them back together in the correct order
    barcode_blocks = [ create_barcode(chunk) for chunk in create_chunks(ascdata, max_bytes_in_barcode) ]

    if USE_REPORTLAB:

        font_name = search_DPCustomMono2_font()
        c = canvas.Canvas(input_path+".pdf",
                          pagesize=paperformat_obj)

        # place barcodes on pages
        pgno = 0   # page number
        ppos = 0   # position id on page
        if font_name: c.setFont(font_name, 9)
        for bc in range(len(barcode_blocks)):
            if ppos >= barcodes_per_page:
                # finish the page
                finish_page(None, c, pgno, USE_REPORTLAB=USE_REPORTLAB)
                c.showPage()
                if font_name: c.setFont(font_name, 9)
                pgno += 1
                ppos = 0

            c.drawString(barcode_x_positions[ppos] + text_x_offset,
                         barcode_y_positions[ppos] + text_y_offset,
                         "%s (%i/%i)" % (just_filename, bc+1, len(barcode_blocks)))
            c.drawImage(ImageReader(barcode_blocks[bc]),
                        barcode_x_positions[ppos],
                        barcode_y_positions[ppos],
                        width=barcode_height,
                        height=barcode_height,)
            ppos += 1
        # finish the last page with barcode(s)
        finish_page(None, c, pgno, USE_REPORTLAB=USE_REPORTLAB)
        c.showPage()
        pgno += 1

        # place plaintext lines with truncated MD5 sums and instructions
        outlines = prepare_plainlines(ascdata, plaintext_maxlinechars)

        if font_name: c.setFont(font_name, 9)
        text = c.beginText(1.5*cm, 27*cm)
        if font_name:
            # minimal vertical separation, empirically based on DPCustomMono2 (9pt) font and the letters combinations
            #  gggg qqqq
            #  IiVW IiVW
            text.setLeading(12)
        for line in outlines:
            logging.debug(text.getStartOfLine()[1]/cm)
            if text.getStartOfLine()[1] < 1.5*cm :
                logging.debug("Minimum reached!")
                c.drawText(text)
                finish_page(None, c, pgno, USE_REPORTLAB=USE_REPORTLAB)
                c.showPage()
                if font_name: c.setFont(font_name, 9)
                pgno += 1
                text = c.beginText(1.5*cm, 27*cm)
            text.textLine(line)

        # finish the last page
        c.drawText(text)
        finish_page(None, c, pgno, USE_REPORTLAB=USE_REPORTLAB)
        c.showPage()
        # Save the PDF file
        c.save()

    else:

        # init PyX
        unit.set(defaultunit=l_unit)
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

        # prepare plain text output
        fd, temp_text_path = mkstemp('.ps', 'text_', '.')
        input_file_modification = datetime.fromtimestamp(os.path.getmtime(input_path)).strftime("%Y-%m-%d %H:%M:%S")

        outlines = prepare_plainlines(ascdata, plaintext_maxlinechars)

        # use "enscript" to create postscript with the plaintext
        p = subprocess.Popen(
                ["enscript", "-p"+temp_text_path, "-f", "Courier12",
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

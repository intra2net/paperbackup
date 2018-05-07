# paperbackup.py

Create a pdf with barcodes to backup text files on paper.
Designed to backup ASCII-armored GnuPG and SSH key files and ciphertext.

## How to use

###### Backup

```
gpg2 --armor --export-options export-minimal --export-secret-key "User Name" >key.asc
paperbackup.py key.asc
paperrestore.sh key.asc.pdf | diff key.asc -
lpr key.asc.pdf
```

This will print out the public and private key of "User Name". The
private key is still encrypted with it's passphrase, so make sure
you don't lose or forget it.

See some example output here:
https://github.com/intra2net/paperbackup/raw/master/example_output.pdf

###### Restore

1. Scan the papers
2. Create one file containing all the pages. zbar supports e.g. PDF, TIFF, PNG, JPG,...
3. `paperrestore.sh scanned.pdf >key.asc`
4. `gpg2 --import key.asc`

If one or more barcodes could not be decoded, try scanning them again. If that does
not work, type in the missing letters from the plaintext output at the end of the pdf.

## Dependencies

### 1. creating a backup with paperbackup.py

Always needed:

- python 3 https://www.python.org/
- python3-pillow https://python-pillow.org/
- python3-qrencode https://github.com/Arachnid/pyqrencode

Apart from the above there are now two possible sets of dependencies for paperbackup.py:

#### 1a. using PyX (as with previous versions)

- PyX http://pyx.sourceforge.net/
- LaTeX (required by PyX) https://www.latex-project.org/
- enscript https://www.gnu.org/software/enscript/
- ghostscript https://www.ghostscript.com/

#### 1b. using reportlab

- reportlab https://www.reportlab.com/

If the reportlab module can be imported it will be automatically preferred.

### 2. restoring with paperrestore.sh

- ZBar http://zbar.sourceforge.net/
- sort https://www.gnu.org/software/coreutils/coreutils.html
- sed https://www.gnu.org/software/sed/

### Font

The DPCustomMono2 font included comes from the Distributed Proofreaders project:
https://www.pgdp.net/wiki/DP_Official_Documentation:Proofreading/DPCustomMono2_Font
It was originally created to aid in distinguishing between visually similar letters when proof reading OCRd text.

If you are using reportlab (see 1b. above) and call paperbackup.py in the git repository or tarball this font
will be automatically used.
Otherwise please copy DPCustomMono2.ttf to any of the following locations to use it:
  ~/.fonts/DPCustomMono2.ttf
  ~/.fonts/DPCustomMono2/DPCustomMono2.ttf
  ~/.local/share/fonts/DPCustomMono2.ttf
  ~/.local/share/fonts/DPCustomMono2/DPCustomMono2.ttf
  /usr/share/fonts/TTF/DPCustomMono2.ttf
  /usr/share/fonts/truetype/DPCustomMono2.ttf
  /usr/X11R6/lib/X11/fonts/ttfonts/DPCustomMono2.ttf
  /usr/X11R6/lib/X11/fonts/DPCustomMono2.ttf

## Why backup on paper?

Some data, like GnuPG or SSH keys, can be really really important for you, like that your whole
business relies on them. If that is the case, you should have multiple backups at multiple
places of it.

I also think it is a good idea to use different media types for it. Hard disks, flash based
media and CD-R are not only susceptible to heat, water and strong EM waves, but also age.

Paper, if properly stored, has proven to be able to be legible after centuries. It is also
quite resistant to fire if stored as a thick stack like a book.

So I think it is a good idea to throw a backup on paper into the mix of locations and media
types of your important backups.

Storing the paper backup in a machine readable format like barcodes makes it practical to restore
even large amounts in short order. If the paper is too damaged for the barcodes to be readable,
you still have the printed plaintext that paperbackup produces.

## How to properly store the paper

The ISO has some standards for preservation and long term storage of paper:

ISO/TC 46/SC 10 - Requirements for document storage and conditions for preservation
http://www.iso.org/iso/home/store/catalogue_tc/catalogue_tc_browse.htm?commid=48842

Here's an example of what ISO 16245 describes:
http://www.iso.org/iso/livelinkgetfile-isocs?nodeId=15011261

## Choice and error resilency of barcodes

Only 2D barcodes have the density to make key backup practical. QR Code and DataMatrix are
the most common 2D barcodes.

Using a common barcode symbology makes sure that there are several independent implementations
of decoders available. This increases the probability that they handle defects and error
correction differently and are able to tolerate different kinds of defects. So if the barcode
gets damaged, you have several programs you can try.

Several papers comparing QR and DataMatrix come to the conclusion that DataMatrix allows
a higher density and offers better means for error correction. I tested this and came
to the conclusion that the QR code decoding programs available to me had better error
resilency than the ones for DataMatrix.

The toughest test I found, other than cutting complete parts from a code, was printing 
the code, scanning it, printing the scanned image on a pure black and white printer 
and then repeating this several times. While the barcode still looks good to the human
eye, this process slightly deforms the barcode in an irregular pattern.

libdmtx was still able to decode a DataMatrix barcode with 3 repetitions of the above
procedure. A expensive commercial library was still able to decode after 5 repetitions.

ZBar and the commercial library could still decode a QR code after 7 repetitions.

A laser printed QR code, completely soaked in dirty water for a few hours, rinsed with
clean water, dried and then scanned, could be decoded by ZBar on the first try.

This is why I chose QR code for this program.

## Encoding and data format

In my tests I found that larger QR codes are more at risk to becoming undecodable due to
wrinkles and deformations of the paper. So paperbackup splits the barcodes at 140 bytes of data.

QR codes offer a feature to concatenate the data of several barcodes. As this is not supported
by all programs, I chose not to use it.

Each barcode is labeled with a start marker `^<sequence number><space>`. After that the raw
and otherwise unencoded data follows.

## Plaintext output

paperbackup prints the plaintext in addition to the QR codes. If decoding one or more barcodes
should fail, you can use it as fallback.

To ease entering large amounts of "gibberish" like base64 data, each line is printed with
a checksum. The checksum is the first 6 hexadecimal characters of MD5 sum of the line content.
The MD5 is on the "pure" line content without the line break (e.g. \n or \r\n)

To verify a line checksum use
`echo -n "line content" | md5sum | cut -c -6`

If a line is too long to be printed on paper, it is split. This is denoted by a "^" character
at the begin of the next line on paper. The "^" is not included in the checksum.

## Changing the paper format

The program writes PDFs in A4 by default. You can uncomment the respective lines
in the constants section of the source to change to US Letter.

## Similar projects

###### PAPERBACK http://ollydbg.de/Paperbak/

Although it is GPL 3, it is currently available for Windows only. It uses it's own proprietary
barcode type. That allows it to produce much more dense code, but in case of a problem with
decoding you are on your own.

###### Twibright Optar http://ronja.twibright.com/optar/

Uses the not-so-common Golay code to backup 200KB per page. So it offers a much higher
density than paperbackup.py, but is probably more affected by defects on the paper.
GPL 2 and designed for Linux.

###### Paperkey http://www.jabberwocky.com/software/paperkey/

It is designed to reduce the data needed to backup a private GnuPG key. It does not help you
to print and scan the data. So it could be used in addition to paperbackup.py.

###### asc2qr.sh https://github.com/4bitfocus/asc-key-to-qr-code

Very similar to paperbackup.py. But it only outputs .png images without ordering information.
So you have to arrange printing and ordering yourself.

## License

MIT X11 License

The font in DPCustomMono2.ttf is covered under its own license, c.f. LICENSE.font

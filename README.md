# paperbackup.py

Create a pdf with barcodes to backup text files on paper.
Designed to backup ASCII-armored GnuPG and SSH key files and ciphertext.

## How to use

###### Backup

```
gpg2 --armor --export "User Name" >key.asc
gpg2 --armor --export-secret-key "User Name" >>key.asc
paperbackup.py key.asc
paperrestore.sh key.asc.pdf | diff key.asc -
lpr key.asc.pdf
```

This will print out the public and private key of "User Name". The
private key is still encrypted with it's passphrase, so make sure
you don't lose or forget it.

See some example output here:

###### Restore

1. Scan the papers
2. Create one file containing all the pages. zbar supports e.g. PDF, TIFF, PNG, JPG,...
3. `paperrestore.sh scanned.pdf >key.asc`
4. `gpg2 --import key.asc`

If one or more barcodes could not be decoded, try scanning them again. If that does
not work, type in the missing letters from the plaintext output at the end of the pdf.

## Dependencies

- python 3 https://www.python.org/
- python3-pillow https://python-pillow.org/
- PyX http://pyx.sourceforge.net/
- LaTeX (required by PyX) https://www.latex-project.org/
- python3-qrencode https://github.com/Arachnid/pyqrencode
- enscript python3-qrencode
- ghostscript https://www.ghostscript.com/
- ZBar http://zbar.sourceforge.net/

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

## Choice and error resilency of barcodes

Only 2D barcodes have the density to make key backup practical. QR Code and DataMatrix are
the most common 2D barcodes.

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

## Changing the paper format

The program writes PDFs in A4 by default. You can uncomment the respective lines
in the constants section of the source to change to US Letter.

## License

MIT X11 License

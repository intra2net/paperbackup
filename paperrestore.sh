#!/bin/bash

# restore data backed up with paperbackup.py

# give one file containing all qrcodes as parameter

SCANNEDFILE=$1

if [ -z "$SCANNEDFILE" ]; then
    echo "give one file containing all qrcodes as parameter"
    exit 1
fi

if ! [ -f "$SCANNEDFILE" ]; then
    echo "$SCANNEDFILE is not a file"
    exit 1
fi

if [ ! -x "/usr/bin/zbarimg" ]; then
    echo "/usr/bin/zbarimg missing"
    exit 2
fi

# zbarimg ends each scanned code with a newline

# each barcode content begins with ^<number><space>
# so convert that to \0<number><space>, so sort can sort on that
# then remove all \n\0<number><space> so we get the originial without newlines added

/usr/bin/zbarimg --raw -Sdisable -Sqrcode.enable "$SCANNEDFILE" \
    | sed -e "s/\^/\x0/g" \
    | sort -z -n \
    | sed ':a;N;$!ba;s/\n\x0[0-9]* //g;s/\x0[0-9]* //g;s/\n\x0//g'

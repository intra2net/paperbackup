#!/usr/bin/bash

# USAGE: paperbackup-verify.sh backup.pdf
#   where backup.pdf should be the pdf created with paperbackup.py

RESTOREPROG=$(dirname $0)/paperrestore.sh

rPDF=$( $RESTOREPROG $1 )

bPDF=$(echo "$rPDF" | b2sum | cut -d ' ' -f 1 )
bEmbedded=$(pdftotext $1 - | grep b2sum -A2 | tail -2 | tr -d '\n')

if [ "x$bPDF" == "x$bEmbedded" ]; then
    echo "b2sums MATCH :-)"
    echo
    exit 0
else
    echo "Creating diff:"
    echo "$rPDF" | diff ${1%.*} -
    diffret=$?
    echo
    if [ $diffret -ne 0 ]; then
        echo "diff and b2sums do NOT match!"
        echo "restored b2sum from PDF: " $bPDF
        echo "original b2sum embedded: " $bEmbedded
        echo
        exit 11
    else
        echo "diff matches but b2sum is missing."
        echo
        exit 1
    fi
fi

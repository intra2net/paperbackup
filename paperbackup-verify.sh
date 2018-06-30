#!/bin/bash

# USAGE: paperbackup-verify.sh backup.pdf
#   where backup.pdf should be the pdf created with paperbackup.py

RESTOREPROG=$(dirname $0)/paperrestore.sh

bPDF=$( $RESTOREPROG $1 | sha256sum | cut -d ' ' -f 1)
bEmbedded=$(pdftotext $1 - | grep sha256sum -A1 | tail -1 | tr -d '\n')

if [ "x$bPDF" == "x$bEmbedded" ]; then
    echo "sha256sums MATCH :-)"
    echo
    exit 0
else
    echo "Creating diff:"
    $RESTOREPROG $1 | diff ${1%.*} -
    diffret=$?
    echo
    if [ $diffret -ne 0 ]; then
        echo "diff and sha256sums do NOT match!"
        echo "restored sha256sum from PDF: " $bPDF
        echo "original sha256sum embedded: " $bEmbedded
        echo
        exit 11
    else
        echo "diff matches but sha256sum is missing."
        echo "restored sha256sum from PDF: " $bPDF
        echo "original sha256sum embedded: " $bEmbedded
        echo
        exit 1
    fi
fi

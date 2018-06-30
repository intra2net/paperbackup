#!/bin/bash

# Restores data from scanned pages created with gpg-paperbackup.sh
#
# USAGE: paperrestore-gpg.sh input_fpath output_fpath
#   where input_fpath is path to PDF with scanned paper backup
#   previously created with gpg-paperbackup.sh
#   Decrypted plaintext will be written to output_fpath

PAPERBACKUPPATH="$(readlink -f $(dirname $0))"
${PAPERBACKUPPATH}/paperrestore.sh "$1" | base64 --decode | gpg -d > "$2"

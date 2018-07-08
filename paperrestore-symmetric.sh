#!/usr/bin/env bash

# Restores data from scanned pages created with paperbackup-symmetric.sh
#
# USAGE: paperrestore-symmetric.sh input_fpath output_fpath
#   where input_fpath is path to PDF with scanned paper backup
#   previously created with paperbackup-symmetric.sh
#   Decrypted plaintext will be written to output_fpath.
#   The script uses gpg2 for decryption and falls back to gpg
#   if gpg2 is not available.

set -euf -o pipefail

PAPERBACKUPPATH="$(readlink -f $(dirname $0))"

if ! GPGPATH=$(command -v gpg2) ; then
  if ! GPGPATH=$(command -v gpg) ; then
    echo "ERROR: gpg and gpg2 commands not found"
    exit 1
  fi
fi
echo "${GPGPATH} will be used for encryption"


${PAPERBACKUPPATH}/paperrestore.sh "$1" | base64 --decode | ${GPGPATH} -d > "$2"

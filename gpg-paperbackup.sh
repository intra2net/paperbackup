#!/bin/bash

# Encrypts specified file with gpg default symmetric cipher algorithm
# and prepares paperbackup PDF of encrypted version
#
# USAGE: gpg-paperbackup.sh plaintext_fpath output_fpath
#
#   where plaintext_fpath is plaintext file to encode (can be text or binary).
#   encrypted and base64 encoded version of plaintext will be written
#   to output_fpath.
#   The script uses gpg2 for symmetric encryption and falls back to gpg
#   if gpg2 is not available.
#
#   output_encrypted_path will then be passed to paperbackup.py and
#   result written to output_encrypted_path.pdf

PAPERBACKUPPATH="$(readlink -f $(dirname $0))"

if ! GPGPATH=$(command -v gpg2) ; then
  if ! GPGPATH=$(command -v gpg) ; then
    echo "ERROR: gpg and gpg2 commands not found"
    exit 1
  fi
fi
echo "${GPGPATH} will be used for encryption"

${GPGPATH} --symmetric -o- "$1" | base64 > "$2"
${PAPERBACKUPPATH}/paperbackup.py "$2"
${PAPERBACKUPPATH}/paperbackup-verify.sh "${2}.pdf"


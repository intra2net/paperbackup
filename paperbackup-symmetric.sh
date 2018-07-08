#!/usr/bin/env bash

# Encrypts specified file with gpg default symmetric cipher algorithm
# and prepares paperbackup PDF of encrypted version
#
# USAGE: paperbackup-symmetric.sh plaintext_fpath output_fpath cipher
#    or  paperbackup-symmetric.sh - output_fpath cipher
#
#   where plaintext_fpath is plaintext file to encode (can be text or binary).
#   encrypted and base64 encoded version of plaintext will be written
#   to output_fpath.
#   If first argument is '-' the script reads input data from stdin.
#   The script uses gpg2 for symmetric encryption and falls back to gpg
#   if gpg2 is not available.
#   Encryption algorithm can be specified in third optional argument.
#   Default is AES256.
#
#   output_encrypted_path will then be passed to paperbackup.py and
#   result written to output_encrypted_path.pdf

set -ef -o pipefail

PAPERBACKUPPATH="$(readlink -f $(dirname $0))"

if ! GPGPATH=$(command -v gpg2) ; then
  if ! GPGPATH=$(command -v gpg) ; then
    echo "ERROR: gpg and gpg2 commands not found"
    exit 1
  fi
fi
echo "${GPGPATH} will be used for encryption"

if [ -z "$3" ] ; then
  CIPHER_ALGO="AES256"
else
  CIPHER_ALGO="$3"
fi

if [ $1 = "-" ]; then
  ${GPGPATH} --symmetric --cipher-algo $CIPHER_ALGO <&0 | base64 > "$2"
else
  ${GPGPATH} --symmetric --cipher-algo $CIPHER_ALGO -o- "$1" | base64 > "$2"
fi
${PAPERBACKUPPATH}/paperbackup.py "$2"
bash ${PAPERBACKUPPATH}/paperbackup-verify.sh "${2}.pdf"


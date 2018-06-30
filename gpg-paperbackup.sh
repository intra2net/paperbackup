#!/bin/bash

# Encrypts specified file with gpg default symmetric cipher algorithm
# and prepares paperbackup PDF of encrypted version
#
# USAGE: gpg-paperbackup.sh plaintext_fpath output_fpath
#   where plaintext_fpath is plaintext file to encode (can be text or binary)
#         encrypted and base64 encoded version of plaintext will be written
#         to output_fpath
#
#   output_encrypted_path will then be passed to paperbackup.py and 
#   result written to output_encrypted_path.pdf

PAPERBACKUPPATH="$(readlink -f $(dirname $0))"
gpg --symmetric -o- "$1" | base64 > "$2"
${PAPERBACKUPPATH}/paperbackup.py "$2"
${PAPERBACKUPPATH}/paperbackup-verify.sh "${2}.pdf"


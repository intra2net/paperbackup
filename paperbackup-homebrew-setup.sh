#!/usr/bin/env bash

set -e

brew install --cask basictex
brew install \
    enscript ghostscript gnu-sed imagemagick libqrencode pillow python3

python3 -m pip install --upgrade pip
python3 -m pip install --upgrade setuptools

# the homebew zbar package interferes with the compilation of zbar-py
brew uninstall zbar --force

CFLAGS="-I$(brew --prefix)/include" LDFLAGS="-L$(brew --prefix)/lib" pip3 install qrencode pyx zbar-py

# (re)install the zbar package to provide the zbarimg binary
brew install zbar

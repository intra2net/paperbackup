# paperbackup Dockerfile
# Copyright (C) 2024, Kamal Mostafa <kamal@whence.com>
# License: MIT License as per <https://github.com/intra2net/paperbackup.git>

# https://github.com/intra2net/paperbackup/issues/19
# Use python:3.9 because:
#   qrencode on python >=3.10 fails with:
#     SystemError: PY_SSIZE_T_CLEAN macro must be defined for '#' formats

FROM python:3.9-bookworm

# dependencies
RUN apt update && apt-get install -y --no-install-recommends \
        libqrencode-dev enscript ghostscript zbar-tools texlive poppler-utils
RUN pip3 install pillow pyx qrencode

# https://github.com/intra2net/paperbackup/issues/10
# Preclude ERROR: attempt to perform an operation not allowed by the security policy `gs'
# https://stackoverflow.com/questions/70655631/imagemagick-security-policy-error-in-github-workflow
RUN sed -i 's/^.*policy.*coder.*none.*PDF.*//' /etc/ImageMagick-6/policy.xml

# paperbackup
RUN git clone https://github.com/intra2net/paperbackup.git

ENTRYPOINT ["/paperbackup/paperbackup.py"]

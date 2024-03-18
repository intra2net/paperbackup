#!/bin/sh
docker run --rm --volume .:/app --workdir /app paperbackup $*

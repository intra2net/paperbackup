#!/bin/sh
docker run --rm --volume .:/app --workdir /app \
	--entrypoint=/paperbackup/paperbackup-verify.sh paperbackup $*

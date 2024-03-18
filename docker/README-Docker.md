# Dockerized PaperBackup

PaperBackup <https://github.com/intra2net/paperbackup.git> is a command-line tool to create a QR-codes/barcodes to backup text files on paper;
Copyright 2017 by Intra2net AG, Germany.

This Dockerized version encapsulates `paperbackup` within a Docker container, allowing for deployment in various and otherwise incompatible environments.  In particular, this allows `paperbackup` to run on systems with more modern python installations (> 3.9) than the tool may require.

### Building the Docker Image

To build the `paperbackup` Docker image, clone the repository and navigate to the directory containing the Dockerfile -- or simply download the Dockerfile and the pair of shell-scripts from that directory -- then run:

```bash
docker build -t paperbackup .
```

### Running the Tool

Use the included one-liner shell scripts `paperbackup.sh` and `paperbackup-verify.sh` to run the tool within the container:

```bash
./paperbackup.sh <inputfile>
```

```bash
./paperbackup-verify.sh <inputfile.pdf>
```

## License

MIT License as per <https://github.com/intra2net/paperbackup.git>.

This simple Dockerfile was created by Kamal Mostafa <kamal@whence.com>.

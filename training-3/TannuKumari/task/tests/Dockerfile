FROM golang:1.23

WORKDIR /tests

COPY . /tests/

# Answers stay readable only by root; the port runs as uid 65534 in a chroot.
RUN chmod 700 /tests/data && chmod 600 /tests/data/* && chmod 755 /tests/test.sh

FROM golang:1.23

WORKDIR /workspace/repo

# Original Python project (staged without its .git directory).
COPY python-titlecase/ /workspace/repo/

# Fail the build if the expected Go toolchain is not available.
RUN go version

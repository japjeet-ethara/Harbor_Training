# Pinned toolchain image: the same "room" every time (Go 1.23, Debian bookworm).
FROM golang:1.23

# The original Python project, copied from this folder (no .git directory).
# Source: https://github.com/ppannuto/python-titlecase  @ 42f43e2de55bf003b286c6f8e8d8b2d26676a167 (MIT)
COPY python-titlecase /workspace/repo

WORKDIR /workspace/repo

# Pinned base image: Go 1.23 toolchain (not :latest).
FROM golang:1.23

# The original Python project, copied without its .git folder.
# Docker can only COPY from inside the build context, so the repo lives in
# environment/python-titlecase (a copy of ../python-titlecase at the SHA in NOTES.md).
COPY python-titlecase/ /workspace/repo/

WORKDIR /workspace/repo

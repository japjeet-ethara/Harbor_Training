# syntax=docker/dockerfile:1
FROM golang:1.23

# The reference implementation lives next to this task folder:
#   <context>/python-titlecase   (the repo)
#   <context>/titlecase-go       (this task)
# Copy its contents into the image, leaving the .git directory behind.
# Build context must be the folder containing both `python-titlecase/` and
# `titlecase-go/`.
COPY --exclude=.git python-titlecase/ /workspace/repo/

WORKDIR /workspace/repo

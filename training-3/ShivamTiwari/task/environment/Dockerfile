# syntax=docker/dockerfile:1
FROM golang:1.23

# Context root is the workspace that contains python-titlecase.
# Docker strips a leading ../, so this copies ./python-titlecase.
# --exclude keeps the repository .git directory out of the image.
COPY --exclude=.git --exclude=.git/** ../python-titlecase /workspace/repo

WORKDIR /workspace/repo

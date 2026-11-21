# syntax=docker/dockerfile:1.19
FROM golang:1.23

COPY --exclude=.git --exclude=.git/** ../python-titlecase /workspace/repo

WORKDIR /workspace/repo

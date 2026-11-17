# syntax=docker/dockerfile:1

# Stage 1: fetch the pinned pyfiglet source and finish its font setup.
FROM alpine:3.20 AS source

RUN apk add --no-cache git

RUN git clone https://github.com/pwaller/pyfiglet /src \
 && cd /src \
 && git checkout 255827efbc09d662875dad50fa0edc1e1263bf45 \
 && rm -rf .git pyfiglet/fonts-contrib test-fonts \
 && mkdir -p pyfiglet/fonts \
 && cp pyfiglet/fonts-standard/* pyfiglet/fonts/

# Stage 2: the room the agent works in. No Python, no git, non-root user.
FROM golang:1.23-alpine

RUN apk add --no-cache bash

RUN adduser -D -u 1000 -s /bin/bash player \
 && mkdir -p /workspace

ENV CGO_ENABLED=0 \
    GOTOOLCHAIN=local

COPY --from=source --chown=player:player /src /workspace/repo

USER player
WORKDIR /workspace/repo

# Agent workspace: Go 1.23 toolchain + the original python-titlecase source.
# Pinned tag (never :latest) so every trial starts in the same room.
# To pin harder, replace the tag with its digest on a machine that can reach Docker Hub:
#   docker buildx imagetools inspect golang:1.23-bookworm   ->  FROM golang:1.23-bookworm@sha256:<digest>
FROM golang:1.23-bookworm

# Build with the image's own toolchain only; never download a newer Go or modules.
ENV GOTOOLCHAIN=local \
    GOPROXY=off \
    GOFLAGS=-mod=readonly \
    CGO_ENABLED=0

# Non-root agent user: cannot touch anything outside its workspace and home.
RUN useradd --create-home --shell /bin/bash agent

# python-titlecase @ 42f43e2de55bf003b286c6f8e8d8b2d26676a167 (MIT), without .git
COPY --chown=agent:agent python-titlecase/ /workspace/repo/

WORKDIR /workspace/repo

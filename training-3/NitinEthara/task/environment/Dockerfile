# The room the agent works in: a pinned Go toolchain plus the Python repo to port.
FROM golang:1.23

# Never let `go` try to download a different toolchain.
ENV GOTOOLCHAIN=local GOPROXY=off GOFLAGS=-mod=mod

# ../python-titlecase (without .git) was copied next to this Dockerfile because
# Docker can only COPY from inside the build context (this folder).
COPY python-titlecase /workspace/repo

WORKDIR /workspace/repo

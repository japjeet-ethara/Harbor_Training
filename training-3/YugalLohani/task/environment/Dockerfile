# The agent's room: Go 1.23 (pinned by digest) plus a copy of python-titlecase at
# commit 42f43e2de55bf003b286c6f8e8d8b2d26676a167, without its .git folder.
# The build context is environment/, so the repository is vendored here as
# environment/python-titlecase/ (a `git archive` of that commit).
FROM golang:1.23@sha256:60deed95d3888cc5e4d9ff8a10c54e5edc008c6ae3fba6187be6fb592e19e8c0

# Use the Go 1.23 toolchain in the image; never download another one.
ENV GOTOOLCHAIN=local

COPY python-titlecase/ /workspace/repo/
WORKDIR /workspace/repo

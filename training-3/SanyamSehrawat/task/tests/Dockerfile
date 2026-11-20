# Verifier image. Same Go toolchain as the agent image so the build check sees the same compiler.
FROM golang@sha256:60deed95d3888cc5e4d9ff8a10c54e5edc008c6ae3fba6187be6fb592e19e8c0

ENV GOTOOLCHAIN=local GOPROXY=off GOFLAGS=-mod=mod CGO_ENABLED=0

COPY . /tests/

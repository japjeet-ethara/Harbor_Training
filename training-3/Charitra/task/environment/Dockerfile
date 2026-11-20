# Official multi-platform Go 1.23 index resolved from Docker Hub on 2026-11-06.
FROM golang:1.23@sha256:60deed95d3888cc5e4d9ff8a10c54e5edc008c6ae3fba6187be6fb592e19e8c0

ENV GOTOOLCHAIN=local GOPROXY=off GOSUMDB=off CGO_ENABLED=0 GOWORK=off
RUN useradd --create-home --uid 1000 --shell /bin/bash agent \
    && mkdir -p /workspace/repo \
    && chown agent:agent /workspace/repo
WORKDIR /workspace/repo
COPY --chown=agent:agent repo/ /workspace/repo/
COPY --chown=agent:agent visible/ /workspace/repo/visible/
USER agent

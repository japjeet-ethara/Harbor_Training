FROM golang:1.23@sha256:60deed95d3888cc5e4d9ff8a10c54e5edc008c6ae3fba6187be6fb592e19e8c0
RUN useradd --uid 1000 --create-home --shell /bin/bash candidate \
    && install -d -o candidate -g candidate /workspace/repo
ENV GOTOOLCHAIN=local GOWORK=off GOENV=off GOPROXY=off GOSUMDB=off CGO_ENABLED=0 GOTELEMETRY=off
COPY --chown=candidate:candidate repo/ /workspace/repo/
WORKDIR /workspace/repo

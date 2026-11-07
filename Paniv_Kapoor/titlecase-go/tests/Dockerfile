FROM python:3.12-slim

COPY --from=golang:1.23 /usr/local/go /usr/local/go
COPY --from=ghcr.io/astral-sh/uv:0.9.7 /uv /uvx /usr/local/bin/

ENV PATH="/usr/local/go/bin:${PATH}"
ENV GOTOOLCHAIN=local
ENV GOCACHE=/tmp/go-cache
ENV GOPATH=/tmp/gopath

RUN mkdir -p /workspace /logs/verifier /tmp/go-cache /tmp/gopath

WORKDIR /workspace

COPY . /tests/
RUN chmod +x /tests/test.sh

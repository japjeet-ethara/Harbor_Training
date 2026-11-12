FROM python:3.12-slim

COPY --from=golang:1.23 /usr/local/go /usr/local/go
ENV GOROOT=/usr/local/go
ENV PATH="/usr/local/go/bin:/go/bin:${PATH}"

COPY --from=ghcr.io/astral-sh/uv:0.9.7 /uv /usr/local/bin/uv

WORKDIR /workspace/repo

COPY . /tests/

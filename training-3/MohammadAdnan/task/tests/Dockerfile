FROM python:3.12-slim

COPY --from=golang:1.23 /usr/local/go /usr/local/go
ENV PATH="/usr/local/go/bin:/usr/local/bin:/usr/bin:/bin"

COPY --from=ghcr.io/astral-sh/uv:0.9.7 /uv /usr/local/bin/uv
COPY --from=ghcr.io/astral-sh/uv:0.9.7 /uvx /usr/local/bin/uvx

COPY . /tests/

RUN ls -la /tests && test -f /tests/test.sh && test -f /tests/behaviour.py
RUN mkdir -p /workspace/repo
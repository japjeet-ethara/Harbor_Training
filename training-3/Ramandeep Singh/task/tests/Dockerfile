FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.9.7 /uv /uvx /usr/local/bin/
COPY --from=golang:1.23 /usr/local/go /usr/local/go
ENV PATH="/usr/local/go/bin:${PATH}"

WORKDIR /app

COPY . /tests/

# Lock down tests directory so only root (the verifier) can access test data
RUN chmod 700 /tests && chmod -R 600 /tests/data

# Restrict Python runtime execution to root only (prevents unprivileged binary from calling python3)
RUN chmod 700 /usr/local/bin/python* /usr/bin/python* 2>/dev/null || true

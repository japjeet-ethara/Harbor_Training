# Verifier image: Python 3.12 (for Reward Kit) + the same Go 1.23 toolchain as the agent's image.
FROM python:3.12-bookworm
COPY --from=golang:1.23 /usr/local/go /usr/local/go
COPY --from=ghcr.io/astral-sh/uv:0.9.0 /uv /uvx /bin/
ENV PATH="/usr/local/go/bin:${PATH}"

WORKDIR /app

COPY . /tests/

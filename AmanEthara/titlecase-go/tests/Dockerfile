FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.9.7 /uv /usr/local/bin/uv
COPY --from=ghcr.io/astral-sh/uv:0.9.7 /uvx /usr/local/bin/uvx
COPY --from=golang:1.23 /usr/local/go /usr/local/go
ENV PATH="/usr/local/go/bin:${PATH}"

RUN uv pip install --system harbor-rewardkit==0.2.4

WORKDIR /app

COPY . /tests/

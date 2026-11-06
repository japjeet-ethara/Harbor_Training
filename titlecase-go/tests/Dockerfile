FROM python:3.12-slim

COPY --from=golang:1.23 /usr/local/go /usr/local/go
ENV PATH="/usr/local/go/bin:${PATH}" \
    GOTOOLCHAIN=local

COPY --from=ghcr.io/astral-sh/uv:0.9.7 /uv /usr/local/bin/uv

RUN uv pip install --system pytest==8.4.1 pytest-json-ctrf==0.3.5

WORKDIR /app

COPY . /tests/

FROM golang:1.23 AS go

FROM python:3.12-slim

COPY --from=go /usr/local/go /usr/local/go
ENV PATH="/usr/local/go/bin:${PATH}"

COPY --from=ghcr.io/astral-sh/uv:0.9.7 /uv /usr/local/bin/uv

RUN uv pip install --system harbor-rewardkit==0.2.*

WORKDIR /app

COPY . /tests/

FROM golang:1.23-bookworm AS go

FROM python:3.12-slim-bookworm

COPY --from=go /usr/local/go /usr/local/go

ENV GOROOT=/usr/local/go
ENV PATH="/usr/local/go/bin:${PATH}"

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential fuse-overlayfs \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir 'harbor-rewardkit>=0.2.4'

WORKDIR /app

COPY . /tests/

FROM python:3.12-slim@sha256:4840d514c583a4d3d8cad3940e68dee6f0f6f3635c12fcd0a3d74c21a5b93a54

COPY --from=ghcr.io/astral-sh/uv:0.9.7 /uv /usr/local/bin/uv

COPY --from=golang:1.23@sha256:60deed95d3888cc5e4d9ff8a10c54e5edc008c6ae3fba6187be6fb592e19e8c0 /usr/local/go /usr/local/go

ENV PATH=/usr/local/go/bin:$PATH GOTOOLCHAIN=local CGO_ENABLED=0 GOCACHE=/tmp/gocache GOPATH=/tmp/gopath

RUN uv pip install --system harbor-rewardkit==0.2.2

WORKDIR /app

COPY . /tests/
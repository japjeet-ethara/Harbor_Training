FROM python:3.12-slim

COPY --from=golang:1.23 /usr/local/go /usr/local/go
RUN ln -sf /usr/local/go/bin/go /usr/local/bin/go \
    && ln -sf /usr/local/go/bin/gofmt /usr/local/bin/gofmt
ENV CGO_ENABLED=0
ENV GOTOOLCHAIN=local
ENV PATH="/usr/local/go/bin:${PATH}"

COPY --from=ghcr.io/astral-sh/uv:0.9.7 /uv /usr/local/bin/uv
COPY --from=ghcr.io/astral-sh/uv:0.9.7 /uv /usr/local/bin/uvx

RUN uv pip install --system pytest==8.4.1 pytest-json-ctrf==0.3.5 \
    && mkdir -p /workspace/repo

WORKDIR /app

COPY . /tests/

FROM golang:1.23

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:0.9.7 /uv /uvx /bin/

RUN mkdir -p /workspace /app /logs/verifier

WORKDIR /app

COPY . /tests/

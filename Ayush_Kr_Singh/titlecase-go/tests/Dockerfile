FROM golang:1.23

COPY --from=ghcr.io/astral-sh/uv:0.6 /uv /uvx /usr/local/bin/

COPY . /tests/
RUN chmod +x /tests/test.sh

WORKDIR /workspace/repo

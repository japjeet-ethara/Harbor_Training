FROM golang:1.23

COPY --from=ghcr.io/astral-sh/uv:0.9.7 /uv /uvx /usr/local/bin/

WORKDIR /workspace/repo

COPY . /tests/

RUN useradd --create-home --shell /bin/sh runner \
    && chmod -R go-rwx /tests

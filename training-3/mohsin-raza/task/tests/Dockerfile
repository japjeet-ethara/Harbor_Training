FROM golang:1.23

# uv/uvx are used to download Reward Kit when the verifier runs (needs network access).
COPY --from=ghcr.io/astral-sh/uv:0.9.7 /uv /uvx /usr/local/bin/

ENV GOTOOLCHAIN=local

WORKDIR /workspace/repo
COPY . /tests/

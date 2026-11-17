# syntax=docker/dockerfile:1.7
FROM golang:1.23.12-bookworm@sha256:167053a2bb901972bf2c1611f8f52c44d5fe7e762e5cab213708d82c421614db AS toolchain
FROM python:3.12.14-slim-bookworm@sha256:392307d22300de8b5986851a12d9176dfc0fc073e65bf6523ebd7dcbeb23564e
ENV PATH="/usr/local/go/bin:${PATH}" GOTOOLCHAIN=local PYTHONDONTWRITEBYTECODE=1
RUN --mount=type=bind,from=toolchain,source=/usr/local/go,target=/mnt/go \
    --mount=type=bind,source=requirements.txt,target=/tmp/requirements.txt \
    --mount=type=secret,id=proxy_ca \
    set -eu; cp -a /mnt/go /usr/local/go; \
    if [ -f /run/secrets/proxy_ca ]; then export PIP_CERT=/run/secrets/proxy_ca; fi; \
    python3 -m pip install --no-cache-dir -r /tmp/requirements.txt; \
    useradd --no-create-home --uid 10001 --shell /usr/sbin/nologin candidate; \
    mkdir -p /logs/verifier /workspace/repo
ENV CGO_ENABLED=0 GOPROXY=off GOSUMDB=off
COPY --chmod=700 . /tests/
WORKDIR /workspace/repo

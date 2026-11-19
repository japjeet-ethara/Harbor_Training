FROM python:3.12-slim

# Go toolchain for the build and behaviour checks.  The task targets linux/amd64.
ARG GO_VERSION=1.23.12
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl \
    && rm -rf /var/lib/apt/lists/* \
    && curl -fsSL "https://go.dev/dl/go${GO_VERSION}.linux-amd64.tar.gz" -o /tmp/go.tar.gz \
    && tar -C /usr/local -xzf /tmp/go.tar.gz \
    && rm /tmp/go.tar.gz \
    && /usr/local/go/bin/go version

ENV PATH="/usr/local/go/bin:${PATH}" \
    GOTOOLCHAIN=local \
    GOCACHE=/tmp/go-build-cache

# Pre-warm the Go build cache so the timed verifier does not rebuild the
# standard library from scratch.
RUN mkdir -p /tmp/go-warm \
    && cd /tmp/go-warm \
    && printf 'package main\n\nfunc main() {}\n' > main.go \
    && go mod init warmup >/dev/null \
    && go build ./... \
    && cd / \
    && rm -rf /tmp/go-warm

# Pinned so verifier execution never needs the network.
RUN python -m pip install --no-cache-dir "harbor-rewardkit==0.2.4"

WORKDIR /tests

COPY . /tests/

RUN chmod +x /tests/test.sh

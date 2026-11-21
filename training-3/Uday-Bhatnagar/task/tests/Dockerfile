FROM golang:1.23 AS go
FROM python:3.14-slim

COPY --from=go /usr/local/go /usr/local/go

ENV PATH="/usr/local/go/bin:${PATH}" \
    GOTOOLCHAIN=local \
    CGO_ENABLED=0 \
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

WORKDIR /tests

COPY . /tests/

RUN chmod +x /tests/test.sh

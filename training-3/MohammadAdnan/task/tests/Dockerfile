# Verifier room: Go on Alpine, NO Python, so a Go wrapper that calls python3 cannot work here.
# The grader itself is Go (tests/checks), standard library only, no network needed.
FROM golang:1.23-alpine@sha256:383395b794dffa5b53012a212365d40c8e37109a626ca30d6151c8348d380b5f
RUN apk add --no-cache bash
ENV CGO_ENABLED=0 \
    GOTOOLCHAIN=local
COPY . /tests/
RUN chmod +x /tests/test.sh && mkdir -p /workspace/repo /logs/verifier
WORKDIR /tests

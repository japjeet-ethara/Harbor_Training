FROM golang:1.23 AS go
FROM python:3.12-slim

COPY --from=go /usr/local/go /usr/local/go
ENV PATH="/usr/local/go/bin:${PATH}" \
    GOROOT="/usr/local/go" \
    CGO_ENABLED="0"

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/*
RUN python -m pip install --no-cache-dir harbor-rewardkit==0.2.4
RUN mkdir -p /workspace/repo /tests/data
WORKDIR /workspace/repo
COPY audit.go /tmp/titlecase-audit.go
RUN CGO_ENABLED=0 GO111MODULE=off go build \
    -o /usr/local/bin/titlecase-audit /tmp/titlecase-audit.go \
    && rm /tmp/titlecase-audit.go
COPY test.sh behaviour.py reward.toml /tests/
COPY data/hidden_inputs.txt data/hidden_expected.txt /tests/data/
RUN chmod +x /tests/test.sh

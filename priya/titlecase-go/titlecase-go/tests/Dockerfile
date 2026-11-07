FROM golang:1.23 AS go-binary

FROM python:3.12-slim

# Copy Go toolchain from the official Go image
COPY --from=go-binary /usr/local/go /usr/local/go
ENV PATH="/usr/local/go/bin:${PATH}"

RUN pip install --no-cache-dir 'harbor-rewardkit>=0.2.4'

WORKDIR /workspace/repo

COPY . /tests/

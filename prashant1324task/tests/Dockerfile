FROM golang:1.23 AS go

FROM python:3.12-slim

COPY --from=go /usr/local/go /usr/local/go

ENV PATH="/usr/local/go/bin:${PATH}"

RUN pip install --no-cache-dir harbor-rewardkit==0.2.*

RUN mkdir -p /workspace && ln -s /workspace/repo /app

WORKDIR /app

COPY . /tests/

FROM golang:1.23 AS go

FROM python:3.12-slim

COPY --from=go /usr/local/go /usr/local/go
ENV GOROOT=/usr/local/go
ENV PATH="/usr/local/go/bin:${PATH}"

WORKDIR /app

COPY . /tests/

FROM alpine:3.21 AS source

RUN apk add --no-cache git \
    && git clone https://github.com/pwaller/pyfiglet /src \
    && git -C /src checkout 255827efbc09d662875dad50fa0edc1e1263bf45 \
    && rm -rf /src/.git /src/pyfiglet/fonts-contrib /src/test-fonts \
    && mkdir -p /src/pyfiglet/fonts \
    && cp -a /src/pyfiglet/fonts-standard/. /src/pyfiglet/fonts/

FROM golang:1.23-alpine

RUN apk add --no-cache bash \
    && adduser -D -u 1000 player

COPY --from=source --chown=player:player /src /workspace/repo

ENV CGO_ENABLED=0
ENV GOTOOLCHAIN=local

WORKDIR /workspace/repo
USER player

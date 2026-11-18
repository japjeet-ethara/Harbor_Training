FROM python:3.12.8-slim-bookworm AS source-preparation

RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

RUN git clone https://github.com/pwaller/pyfiglet.git /src/pyfiglet \
    && git -C /src/pyfiglet checkout 255827efbc09d662875dad50fa0edc1e1263bf45 \
    && rm -rf /src/pyfiglet/.git \
    && rm -rf /src/pyfiglet/fonts-contrib /src/pyfiglet/test-fonts \
    && mkdir -p /src/pyfiglet/pyfiglet/fonts \
    && cp -a /src/pyfiglet/pyfiglet/fonts-standard/. /src/pyfiglet/pyfiglet/fonts/

FROM golang:1.23-alpine AS final

RUN apk add --no-cache bash \
    && addgroup -g 1000 player \
    && adduser -D -u 1000 -G player player

COPY --from=source-preparation --chown=player:player /src/pyfiglet/ /workspace/repo/

ENV CGO_ENABLED=0 \
    GOTOOLCHAIN=local

USER player
WORKDIR /workspace/repo

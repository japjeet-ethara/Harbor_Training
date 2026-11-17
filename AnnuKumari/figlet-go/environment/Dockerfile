FROM alpine/git@sha256:2306e2b05ee0ef99f5d25b0779f645b24ae9f91ba187107503592fcdfe78da3a AS source

RUN git clone https://github.com/pwaller/pyfiglet /src \
    && git -C /src checkout 255827efbc09d662875dad50fa0edc1e1263bf45 \
    && rm -rf /src/.git /src/pyfiglet/fonts-contrib /src/test-fonts \
    && mkdir /src/pyfiglet/fonts \
    && cp /src/pyfiglet/fonts-standard/* /src/pyfiglet/fonts/

FROM golang:1.23-alpine@sha256:383395b794dffa5b53012a212365d40c8e37109a626ca30d6151c8348d380b5f

RUN apk add --no-cache bash \
    && adduser -D -u 1000 -s /bin/bash player

COPY --from=source --chown=player:player /src /workspace/repo

ENV CGO_ENABLED=0 \
    GOTOOLCHAIN=local

USER player
WORKDIR /workspace/repo

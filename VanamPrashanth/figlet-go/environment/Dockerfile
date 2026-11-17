# Stage 1: Fetch and prepare pyfiglet source
FROM alpine/git:2.47.2 AS source

RUN git clone https://github.com/pwaller/pyfiglet /src && \
    cd /src && \
    git checkout 255827efbc09d662875dad50fa0edc1e1263bf45 && \
    rm -rf .git pyfiglet/fonts-contrib test-fonts && \
    mkdir -p pyfiglet/fonts && \
    cp pyfiglet/fonts-standard/* pyfiglet/fonts/

# Stage 2: The agent's room
FROM golang:1.23-alpine

RUN apk add --no-cache bash && \
    adduser -D -u 1000 player

COPY --chown=player:player --from=source /src /workspace/repo

ENV CGO_ENABLED=0 \
    GOTOOLCHAIN=local

USER player
WORKDIR /workspace/repo

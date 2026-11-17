# Stage 1 ("source"): fetch pyfiglet at a pinned commit and finish the project's own font setup.
# Only /src leaves this stage, so git never reaches the room the agent works in.
FROM alpine/git:2.54.1@sha256:2306e2b05ee0ef99f5d25b0779f645b24ae9f91ba187107503592fcdfe78da3a AS source
RUN git clone https://github.com/pwaller/pyfiglet /src \
 && cd /src \
 && git checkout 255827efbc09d662875dad50fa0edc1e1263bf45 \
 && rm -rf .git pyfiglet/fonts-contrib test-fonts \
 && mkdir pyfiglet/fonts \
 && cp pyfiglet/fonts-standard/* pyfiglet/fonts/

# Stage 2: the room. Go only: no Python and no git. bash is added because Harbor runs its commands with it.
FROM golang:1.23-alpine@sha256:383395b794dffa5b53012a212365d40c8e37109a626ca30d6151c8348d380b5f
RUN apk add --no-cache bash \
 && adduser -D -u 1000 player
COPY --from=source --chown=player:player /src /workspace/repo
ENV CGO_ENABLED=0 \
    GOTOOLCHAIN=local
USER player
WORKDIR /workspace/repo

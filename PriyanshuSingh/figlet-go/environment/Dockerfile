# Stage 1 ("source"): fetch pyfiglet at a pinned commit and finish the
# project's own setup. git and its tools never reach the agent's room.
FROM alpine/git:v2.47.2@sha256:062a01ad7a0eb17cff382bc5e26086b4d710e56dfdfdf001109a49b6d9bd378c AS source
WORKDIR /src
RUN git clone https://github.com/pwaller/pyfiglet . \
 && git checkout 255827efbc09d662875dad50fa0edc1e1263bf45 \
 && rm -rf .git pyfiglet/fonts-contrib test-fonts
# The code loads fonts from pyfiglet/fonts/, but the repo ships them in
# pyfiglet/fonts-standard/. This is the Makefile's "clean" + "minimal" copy.
RUN rm -rf pyfiglet/fonts \
 && mkdir pyfiglet/fonts \
 && cp pyfiglet/fonts-standard/* pyfiglet/fonts/

# Stage 2: the agent's room. Go on Alpine (no Python), bash for Harbor,
# and a normal user who owns the repository.
FROM golang:1.23-alpine@sha256:383395b794dffa5b53012a212365d40c8e37109a626ca30d6151c8348d380b5f
RUN apk add --no-cache bash \
 && adduser -D -u 1000 player
COPY --from=source --chown=player:player /src /workspace/repo
ENV CGO_ENABLED=0 \
    GOTOOLCHAIN=local
USER player
WORKDIR /workspace/repo

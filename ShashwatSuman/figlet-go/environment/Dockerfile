# ---------------------------------------------------------------- stage 1
# "source": fetch pyfiglet at a pinned commit and finish its own setup.
# git and everything else from this stage never reach the agent's room (D1).
FROM alpine/git:2.47.2@sha256:062a01ad7a0eb17cff382bc5e26086b4d710e56dfdfdf001109a49b6d9bd378c AS source

RUN git clone https://github.com/pwaller/pyfiglet /src \
    && cd /src \
    && git checkout 255827efbc09d662875dad50fa0edc1e1263bf45 \
    && rm -rf .git pyfiglet/fonts-contrib test-fonts \
    # D3: the Makefile's font setup. The code loads fonts from pyfiglet/fonts/,
    # but the repository ships them in pyfiglet/fonts-standard/.
    && mkdir pyfiglet/fonts \
    && cp pyfiglet/fonts-standard/* pyfiglet/fonts/

# ---------------------------------------------------------------- stage 2
# The agent's room: Go on Alpine, which has NO Python (D2). Pinned by digest (D5).
FROM golang:1.23-alpine@sha256:383395b794dffa5b53012a212365d40c8e37109a626ca30d6151c8348d380b5f

# D6: Harbor runs its commands with bash, and Alpine does not ship it.
RUN apk add --no-cache bash \
    # D4: a normal user, uid 1000, who owns the workspace.
    && adduser -D -u 1000 player \
    && mkdir -p /workspace \
    && chown player:player /workspace

COPY --from=source --chown=player:player /src /workspace/repo

ENV CGO_ENABLED=0 \
    GOTOOLCHAIN=local \
    GOPROXY=off

USER player
WORKDIR /workspace/repo

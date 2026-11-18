# Separate verifier container: Go toolchain (to build the agent's program) + uv (to run Reward Kit).
FROM golang:1.23.4-bookworm

ENV GOTOOLCHAIN=local \
    GOFLAGS=-buildvcs=false

COPY --from=ghcr.io/astral-sh/uv:0.5.14 /uv /uvx /bin/

# Pre-warm uv's cache so verification starts fast (uvx still works if the cache is cold).
RUN uvx --python '>=3.12,<3.14' --from 'harbor-rewardkit==0.2.*' rewardkit --help >/dev/null

WORKDIR /workspace/repo

COPY . /tests/

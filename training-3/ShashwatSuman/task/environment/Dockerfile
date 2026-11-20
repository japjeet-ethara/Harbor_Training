# golang:1.23, pinned to an exact digest so the "room" is identical every time.
FROM golang:1.23@sha256:60deed95d3888cc5e4d9ff8a10c54e5edc008c6ae3fba6187be6fb592e19e8c0

# Python 3 + the `regex` package so the agent can run the original program and
# compare its own Go output against it while it works.
RUN apt-get update \
    && apt-get install -y --no-install-recommends python3 python3-regex \
    && rm -rf /var/lib/apt/lists/*

# No toolchain or module downloads: the agent has no internet, and the task
# requires the Go standard library only.
ENV GOTOOLCHAIN=local \
    GOFLAGS=-mod=mod \
    GOPROXY=off

# The original Python project (copied in without its .git folder).
COPY python-titlecase /workspace/repo

# 2000 example titles and their correct titlecased answers.
COPY examples /workspace/examples

# The agent works as a normal user, not root, so it cannot tamper with
# anything outside its own files.
RUN useradd --create-home --shell /bin/bash agent \
    && chown -R agent:agent /workspace

WORKDIR /workspace/repo

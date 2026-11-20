# The room the agent works in: a pinned Go toolchain, plus the Python project
# to port. python3 + the `regex` package are installed so the agent can run the
# ORIGINAL implementation as a reference while it works (the reference behaviour
# is "with the optional `regex` package installed").
FROM golang:1.23.9-bookworm

RUN apt-get update \
 && apt-get install -y --no-install-recommends python3 python3-regex \
 && rm -rf /var/lib/apt/lists/*

# Offline, reproducible builds: never fetch a newer toolchain or any module.
ENV GOTOOLCHAIN=local \
    GOFLAGS=-buildvcs=false \
    GOPROXY=off

# The repository without its .git folder.
COPY python-titlecase/ /workspace/repo/

WORKDIR /workspace/repo

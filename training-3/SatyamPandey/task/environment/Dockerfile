FROM golang:1.23

# Python is only here so the agent can run the original titlecase() and compare
# against it. python3-regex is the optional `regex` package the original prefers.
RUN apt-get update \
 && apt-get install -y --no-install-recommends python3 python3-regex \
 && rm -rf /var/lib/apt/lists/*

# The repository to port (copied without its .git folder).
COPY python-titlecase /workspace/repo

WORKDIR /workspace/repo

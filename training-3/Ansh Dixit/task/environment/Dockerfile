FROM golang:1.23-bookworm

# python3 is installed so the agent can run the original program as a reference.
# The optional `regex` package is NOT installed, so titlecase uses the stdlib `re` code path.
RUN apt-get update \
 && apt-get install -y --no-install-recommends python3 \
 && rm -rf /var/lib/apt/lists/*

# Non-root agent user: it owns /workspace but cannot touch anything else.
RUN useradd -m -s /bin/bash agent

COPY python-titlecase /workspace/repo
RUN chown -R agent:agent /workspace
WORKDIR /workspace/repo

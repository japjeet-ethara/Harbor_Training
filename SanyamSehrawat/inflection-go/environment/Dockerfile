# golang:1.23 (Go 1.23.12 on Debian 12), pinned by digest so the room is the same every time.
FROM golang:1.23@sha256:60deed95d3888cc5e4d9ff8a10c54e5edc008c6ae3fba6187be6fb592e19e8c0

# python3 lets the agent run the original for reference.
RUN apt-get update \
    && apt-get install -y --no-install-recommends python3 \
    && rm -rf /var/lib/apt/lists/*

# The agent works as a normal user, not root.
RUN useradd --create-home --shell /bin/bash agent

# The original project: inflection 0.5.1 at commit 88eefaa, without .git.
COPY --chown=agent:agent inflection /workspace/repo
RUN chown agent:agent /workspace

WORKDIR /workspace/repo

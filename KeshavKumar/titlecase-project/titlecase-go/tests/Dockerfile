# Verifier image. Harbor builds the separate verifier from THIS file because it
# exists. It must have Go (same pinned image as the agent) to build the agent's
# code, plus uv/uvx to download Reward Kit.
FROM golang:1.23

COPY --from=ghcr.io/astral-sh/uv:0.9.7 /uv /uvx /usr/local/bin/

# Empty by default; Harbor uploads the agent's /workspace/repo artifact here.
WORKDIR /workspace/repo

COPY . /tests/

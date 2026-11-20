# golang:1.23, pinned to an exact digest.
FROM golang:1.23@sha256:60deed95d3888cc5e4d9ff8a10c54e5edc008c6ae3fba6187be6fb592e19e8c0

# Reward Kit is installed at image-build time, so the verifier needs no
# network while it grades.
COPY --from=ghcr.io/astral-sh/uv:0.9.7@sha256:ba4857bf2a068e9bc0e64eed8563b065908a4cd6bfb66b531a9c424c8e25e142 /uv /uvx /usr/local/bin/
ENV UV_TOOL_BIN_DIR=/usr/local/bin \
    UV_TOOL_DIR=/opt/uv-tools \
    UV_PYTHON_INSTALL_DIR=/opt/uv-python
RUN uv tool install --python 3.12 'harbor-rewardkit==0.2.4'

ENV GOTOOLCHAIN=local \
    GOFLAGS=-mod=mod \
    GOPROXY=off

WORKDIR /workspace/repo

COPY . /tests/

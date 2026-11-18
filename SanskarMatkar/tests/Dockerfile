# Verifier container (runs separately from the agent; the agent never sees /tests).
# Same Go toolchain as the agent image, plus Reward Kit pre-installed so grading
# needs no network at all.
FROM golang:1.23-bookworm

ENV GOTOOLCHAIN=local \
    GOPROXY=off \
    GOFLAGS=-mod=readonly \
    CGO_ENABLED=0 \
    UV_INSTALL_DIR=/usr/local/bin \
    UV_TOOL_DIR=/opt/uv/tools \
    UV_TOOL_BIN_DIR=/usr/local/bin \
    UV_PYTHON_INSTALL_DIR=/opt/uv/python

RUN curl -LsSf https://astral.sh/uv/0.9.5/install.sh | sh \
 && uv tool install --python 3.12 'harbor-rewardkit==0.2.4' \
 && rewardkit --help >/dev/null

COPY . /tests/
WORKDIR /tests

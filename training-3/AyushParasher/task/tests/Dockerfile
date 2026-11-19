FROM golang:1.23
COPY --from=ghcr.io/astral-sh/uv:0.9.7 /uv /uvx /usr/local/bin/
ENV UV_TOOL_BIN_DIR=/usr/local/bin
RUN uv tool install --python 3.12 'harbor-rewardkit==0.2.*'
WORKDIR /workspace/repo
COPY . /tests/

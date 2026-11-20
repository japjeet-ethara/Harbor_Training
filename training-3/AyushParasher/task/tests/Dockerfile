FROM golang:1.23
COPY --from=ghcr.io/astral-sh/uv:0.9.7 /uv /uvx /usr/local/bin/
ENV UV_TOOL_BIN_DIR=/usr/local/bin
RUN uv tool install --python 3.12 'harbor-rewardkit==0.2.*'
# No system Python for the port under test to call (rewardkit uses uv's own Python under /root).
RUN rm -f /usr/bin/python3* /usr/local/bin/python3* && ! command -v python3
WORKDIR /workspace/repo
COPY . /tests/

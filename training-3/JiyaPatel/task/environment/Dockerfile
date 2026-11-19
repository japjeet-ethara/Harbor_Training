FROM golang:1.23
RUN apt-get update && apt-get install -y --no-install-recommends python3 curl ca-certificates && rm -rf /var/lib/apt/lists/*
RUN curl -LsSf https://astral.sh/uv/install.sh | env UV_INSTALL_DIR="/usr/local/bin" sh
RUN mkdir -p /workspace/repo
COPY repo /workspace/repo
WORKDIR /workspace/repo

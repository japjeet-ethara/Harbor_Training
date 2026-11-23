FROM golang:1.23

COPY --from=ghcr.io/astral-sh/uv:0.9.7 /uv /usr/local/bin/uv
COPY --from=ghcr.io/astral-sh/uv:0.9.7 /uvx /usr/local/bin/uvx

# Strip Python so the "Python inside" cheat cannot call python3.
# golang:1.23-bookworm is Debian bookworm but has no python3 by default;
# this RUN is an explicit guard in case a base-image update adds it.
RUN apt-get update && apt-get remove -y --auto-remove python3 python3-minimal \
    python3-pip python-is-python3 2>/dev/null || true && \
    rm -rf /var/lib/apt/lists/*

RUN mkdir -p /workspace /app /logs/verifier

# Create unprivileged user for running candidate binaries
RUN useradd -r -s /sbin/nologin candidate

WORKDIR /app

COPY . /tests/

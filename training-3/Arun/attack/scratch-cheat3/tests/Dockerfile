# Same pinned Go image as the agent's environment.
FROM golang:1.23@sha256:60deed95d3888cc5e4d9ff8a10c54e5edc008c6ae3fba6187be6fb592e19e8c0

# Remove the system Python, so a submitted program cannot hand its work to the
# original Python code. (Reward Kit gets its own Python below, under /root, which
# the submitted program cannot reach: it runs as the user `nobody`.)
RUN apt-get purge -y 'python3*' 'libpython3*' \
    && apt-get autoremove -y --purge \
    && rm -rf /var/lib/apt/lists/* \
    && ! command -v python3 \
    && ! command -v python

# uv 0.9.7, pinned by digest.
COPY --from=ghcr.io/astral-sh/uv:0.9.7@sha256:ba4857bf2a068e9bc0e64eed8563b065908a4cd6bfb66b531a9c424c8e25e142 /uv /uvx /usr/local/bin/

# Reward Kit is installed while the image builds, so grading itself needs no network.
ENV UV_TOOL_BIN_DIR=/usr/local/bin
RUN uv tool install --python 3.12 harbor-rewardkit==0.2.4 \
    && chmod 700 /root

# Harbor copies the agent's final /workspace/repo here before test.sh runs.
WORKDIR /workspace/repo

COPY . /tests/

# Only root may read the tests and the answers; the submitted program does not run as root.
RUN chmod -R go-rwx /tests \
    && command -v pkill

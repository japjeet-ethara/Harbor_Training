# Verifier image. Harbor builds the separate verifier from THIS file because it
# exists. It has Go (same pinned image as the agent) to build the agent's code.
FROM golang:1.23

COPY --from=ghcr.io/astral-sh/uv:0.9.7 /uv /uvx /usr/local/bin/

# Reward Kit is installed at BUILD time, so grading needs no network.
# Its Python is uv-managed and lives under /root (mode 700): the user `nobody`,
# which runs the agent's program, cannot reach it. The system python3 is
# removed, so the agent's program has no Python at all.
ENV UV_PYTHON_PREFERENCE=only-managed
RUN uv tool install --python 3.13 'harbor-rewardkit==0.2.4' \
 && apt-get purge -y --auto-remove 'python3*' 'libpython3*' \
 && rm -rf /var/lib/apt/lists/* \
 && /root/.local/bin/rewardkit --help > /dev/null

# Empty by default; Harbor uploads the agent's /workspace/repo artifact here.
WORKDIR /workspace/repo

COPY . /tests/
RUN chmod -R go-rwx /tests

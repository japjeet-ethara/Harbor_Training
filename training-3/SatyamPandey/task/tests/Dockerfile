FROM golang:1.23

# The verifier container has Go (to build the agent's program), Reward Kit (to
# combine the checks) and, in /opt/rk only, the `regex` package: checks/fresh.py runs
# the original titlecase (tests/original) on fresh titles at grading time. regex is
# pinned to the version that froze tests/data/answers.txt (Python 3.12 + this
# version reproduces all 100,000 frozen answers byte for byte).
# Reward Kit needs Python >= 3.12, so uv provides one in /opt/rk (no network is
# needed at grading time). It is installed system-wide (not under /root) because
# Reward Kit's Worker starts the agent's program through it as an unprivileged user;
# the agent's program cannot start programs itself (checks/rules.py).
COPY --from=ghcr.io/astral-sh/uv:0.9.7 /uv /usr/local/bin/uv
ENV UV_PYTHON_INSTALL_DIR=/opt/uv-python
RUN uv venv --python 3.12 /opt/rk \
 && uv pip install --python /opt/rk/bin/python harbor-rewardkit==0.2.4 regex==2026.11.19

WORKDIR /app

# /tests holds the answers; checks/behaviour.py locks it (mode 0700) before the
# agent's program runs.
COPY . /tests/

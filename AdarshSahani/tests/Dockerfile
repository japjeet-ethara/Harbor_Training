FROM golang:1.23

# The verifier container has Go (to build the agent's program) and Reward Kit
# (to combine the checks). It deliberately has NO `regex`/titlecase Python
# package and no copy of the original project.
# Reward Kit needs Python >= 3.12, so uv provides one in /opt/rk (no network is
# needed at grading time).
COPY --from=ghcr.io/astral-sh/uv:0.9.7 /uv /usr/local/bin/uv
ENV UV_PYTHON_INSTALL_DIR=/opt/uv-python
RUN uv venv --python 3.12 /opt/rk \
 && uv pip install --python /opt/rk/bin/python harbor-rewardkit==0.2.4

WORKDIR /app

COPY . /tests/

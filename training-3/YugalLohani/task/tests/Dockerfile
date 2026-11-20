# Separate verifier image. It never reaches the agent: Harbor builds it from
# tests/ and runs it only after the agent has finished. The agent's
# /workspace/repo is copied in as an artifact (task.toml: artifacts).
#
# Same Go toolchain as the agent's room, plus Reward Kit installed at build
# time, so grading needs no network.
FROM golang:1.23@sha256:60deed95d3888cc5e4d9ff8a10c54e5edc008c6ae3fba6187be6fb592e19e8c0

COPY --from=ghcr.io/astral-sh/uv:0.10.9@sha256:10902f58a1606787602f303954cea099626a4adb02acbac4c69920fe9d278f82 /uv /uvx /usr/local/bin/

ENV GOTOOLCHAIN=local \
    UV_PYTHON_INSTALL_DIR=/opt/uv/python \
    UV_TOOL_DIR=/opt/uv/tools \
    UV_TOOL_BIN_DIR=/opt/uv/bin \
    UV_CACHE_DIR=/opt/uv/cache \
    PATH=/opt/uv/bin:$PATH

RUN uv tool install --python 3.12 'harbor-rewardkit==0.2.4' \
 && rewardkit --help >/dev/null \
 # Reward Kit runs on uv's managed Python under /opt/uv; remove the system
 # interpreters a candidate could shell out to (the grader runs candidates
 # with PATH=/usr/local/go/bin:/usr/bin:/bin and these absolute paths gone).
 && rm -f /usr/local/bin/python3* /usr/local/bin/python \
          /usr/bin/python3* /usr/bin/python \
 && ! ls /usr/bin/python3 /usr/bin/python /usr/local/bin/python3 /usr/local/bin/python 2>/dev/null \
 && rewardkit --help >/dev/null \
 # Unprivileged user the grader drops to when running candidate binaries.
 && useradd --uid 1001 --create-home --shell /usr/sbin/nologin runner

COPY . /tests/
# The hidden answers (and inputs) are readable only by the trusted grader,
# which runs as root; the unprivileged "runner" that executes candidates cannot
# read them, so a program cannot print the answer sheet instead of computing it.
RUN chmod 600 /tests/data/hidden_inputs.txt /tests/data/hidden_expected.txt
WORKDIR /tests

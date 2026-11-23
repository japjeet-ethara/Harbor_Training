FROM golang:1.23

COPY --from=ghcr.io/astral-sh/uv:0.6 /uv /uvx /usr/local/bin/

# The verifier itself needs a Python runtime for Reward Kit, so it is installed
# with uv as root. The submitted Go binary is executed as the unprivileged
# "runner" user, which must not be able to start any interpreter.
RUN useradd --create-home --shell /bin/bash runner

# golang:1.23 (buildpack-deps) ships /usr/bin/python3.11. Make every interpreter
# unreadable and unexecutable for "runner"; root can still run uvx.
RUN chmod 700 /usr/bin/python* /usr/local/bin/python* 2>/dev/null || true

# A copied interpreter binary is useless if its standard library is sealed too,
# so the stdlib trees and any shared libpython are root-only for "runner".
RUN chmod 700 /usr/lib/python3* /usr/local/lib/python3* \
      /usr/lib/x86_64-linux-gnu/libpython* 2>/dev/null || true

COPY . /tests/
RUN chmod +x /tests/test.sh && chmod 700 /tests

WORKDIR /workspace/repo

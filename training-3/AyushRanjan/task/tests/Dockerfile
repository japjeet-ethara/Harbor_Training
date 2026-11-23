FROM python:3.12-slim

# The verifier reads answer files as root and runs the candidate as uid 65534.
USER root

COPY --from=golang:1.23 /usr/local/go /usr/local/go
ENV PATH="/usr/local/go/bin:${PATH}"

COPY --from=ghcr.io/astral-sh/uv:0.9.7 /uv /usr/local/bin/uv

COPY --from=ghcr.io/astral-sh/uv:0.9.7 /uvx /usr/local/bin/uvx

RUN uv pip install --system pytest==8.4.1 pytest-json-ctrf==0.3.5

# Keep the verifier's Python available to root, but not to the unprivileged
# candidate process (even when it supplies Python's absolute path).
RUN chmod 700 /usr/local/bin/python3.12

WORKDIR /app

COPY criteria/ /tests/
COPY data/ /tests/data/
COPY test.sh /tests/test.sh

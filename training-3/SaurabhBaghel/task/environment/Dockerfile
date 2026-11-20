FROM golang:1.23-bookworm@sha256:167053a2bb901972bf2c1611f8f52c44d5fe7e762e5cab213708d82c421614db

COPY --from=ghcr.io/astral-sh/uv:0.9.7 /uv /usr/local/bin/uv

RUN uv python install 3.12.12 \
    && uv venv /opt/py --python 3.12.12 \
    && uv pip install --python /opt/py/bin/python --no-cache regex==2024.11.6

ENV PATH="/opt/py/bin:${PATH}"

WORKDIR /workspace/repo

COPY repo/ /workspace/repo/

RUN chmod -R a+rX /workspace/repo

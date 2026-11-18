FROM golang:1.23

COPY --from=ghcr.io/astral-sh/uv:0.9.7 /uv /uvx /usr/local/bin/

ENV UV_PYTHON_INSTALL_DIR=/opt/uv-python
RUN uv python install 3.12

WORKDIR /workspace/repo
COPY . /tests/

FROM golang:1.23

COPY --from=ghcr.io/astral-sh/uv:0.9.7 /uv /uvx /usr/local/bin/

# Reward Kit needs Python 3.12+. It lives where only root can reach it, and the
# system Python is removed, so a submitted program cannot run the original code.
ENV UV_PYTHON_INSTALL_DIR=/opt/uv/python \
    UV_CACHE_DIR=/opt/uv/cache \
    UV_PYTHON_PREFERENCE=only-managed
RUN uv python install 3.12 \
    && chmod 700 /opt/uv \
    && rm -f /usr/bin/python3*

WORKDIR /workspace/repo

COPY . /tests/

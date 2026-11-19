FROM golang:1.23

COPY --from=ghcr.io/astral-sh/uv:0.6 /uv /uvx /usr/local/bin/

# Create unprivileged runner user
RUN useradd --create-home --shell /bin/bash runner

# Restrict permissions on system python if present so runner cannot invoke it
RUN chmod 700 /usr/bin/python* /usr/local/bin/python* 2>/dev/null || true

COPY . /tests/
RUN chmod +x /tests/test.sh && chmod 700 /tests

WORKDIR /workspace/repo

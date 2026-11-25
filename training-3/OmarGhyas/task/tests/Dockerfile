FROM golang:1.23

COPY --from=ghcr.io/astral-sh/uv:0.9.7 /uv /uvx /usr/local/bin/

RUN mkdir -p /workspace/repo /var/grader \
    && chmod 755 /var/grader

WORKDIR /tests
COPY . /tests/

# Root can read the hidden dataset. The program under test runs as nobody
# and cannot traverse this directory.
RUN find /tests -type d -exec chmod 700 {} + \
    && find /tests -type f -exec chmod 600 {} + \
    && chmod 755 /tests/test.sh

FROM golang:1.23

COPY --from=ghcr.io/astral-sh/uv:0.9.7 /uv /uvx /usr/local/bin/

RUN useradd --system --no-create-home --shell /usr/sbin/nologin titlecase

WORKDIR /tests

COPY test.sh test_outputs.py reward.toml /tests/
COPY build /tests/build/
COPY no_python /tests/no_python/
COPY behaviour /tests/behaviour/
COPY data /tests/data/

RUN chown -R root:root /tests \
    && chmod -R 700 /tests \
    && chmod 755 /tests/test.sh

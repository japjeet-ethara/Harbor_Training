FROM python:3.12-slim

COPY --from=golang:1.23 /usr/local/go /usr/local/go
COPY --from=ghcr.io/astral-sh/uv:0.9.7 /uv /usr/local/bin/uv

ENV PATH="/usr/local/go/bin:/root/.local/bin:${PATH}"

RUN uv tool install --python 3.12 harbor-rewardkit==0.2.4

WORKDIR /app

COPY . /tests/

# The agent's program runs in this container as nobody and must not read the answers.
RUN chmod -R go-rwx /tests

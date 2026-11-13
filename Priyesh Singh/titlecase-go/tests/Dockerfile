FROM golang:1.23

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:0.13.7 /uv /uvx /bin/

RUN uv python install 3.12 \
    && uv tool install --python 3.12 "harbor-rewardkit==0.2.*"

ENV PATH="/root/.local/bin:${PATH}"

WORKDIR /app

COPY . /tests/

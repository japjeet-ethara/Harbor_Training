FROM golang:1.23@sha256:60deed95d3888cc5e4d9ff8a10c54e5edc008c6ae3fba6187be6fb592e19e8c0

COPY --from=ghcr.io/astral-sh/uv:0.9.7 /uv /uvx /bin/

RUN uv python install 3.12 \
    && uv tool install --python 3.12 'harbor-rewardkit==0.2.4'

ENV PATH="/root/.local/bin:${PATH}"

WORKDIR /tests
COPY . /tests/
RUN chmod +x /tests/test.sh

# The examiner's room (separate verifier container): Go + Reward Kit.
FROM golang:1.23
ENV GOTOOLCHAIN=local GOFLAGS=-mod=mod GOPROXY=off

COPY --from=ghcr.io/astral-sh/uv:0.9.7 /uv /usr/local/bin/uv
RUN uv venv /opt/rk --python 3.12 \
 && uv pip install --python /opt/rk/bin/python 'harbor-rewardkit==0.2.4'
ENV PATH=/opt/rk/bin:$PATH

WORKDIR /app
COPY . /tests/

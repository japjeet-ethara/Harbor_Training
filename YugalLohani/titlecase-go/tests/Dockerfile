FROM golang:1.23

# Install Python 3 and uv/uvx.
RUN apt-get update && apt-get install -y --no-install-recommends \
        python3 \
        python3-pip \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install uv (provides uvx for running harbor-rewardkit).
COPY --from=ghcr.io/astral-sh/uv:0.9.7 /uv /uvx /usr/local/bin/

# Bundle the tests into the verifier image.
# gen.py and grader.py are included; data/ is generated at container startup
# by test.sh if it doesn't already exist.
COPY . /tests/

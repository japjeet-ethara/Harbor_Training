FROM python:3.12-slim

# Copy Go toolchain from official golang image
COPY --from=golang:1.23 /usr/local/go /usr/local/go
ENV PATH="/usr/local/go/bin:${PATH}"

# Install uv package manager
COPY --from=ghcr.io/astral-sh/uv:0.9.7 /uv /usr/local/bin/uv

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install test dependencies and RewardKit
RUN uv pip install --system \
    pytest==8.4.1 \
    pytest-json-ctrf==0.3.5 \
    'harbor-rewardkit==0.2.*'

WORKDIR /app

COPY . /tests/

RUN chmod +x /tests/test.sh

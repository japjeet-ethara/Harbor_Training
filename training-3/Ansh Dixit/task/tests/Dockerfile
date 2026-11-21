FROM python:3.12-slim

# Go toolchain (same version as the agent image) copied from the official image.
COPY --from=golang:1.23-bookworm /usr/local/go /usr/local/go
ENV PATH=/usr/local/go/bin:$PATH

# Reward Kit is installed at build time so the verifier needs no network.
RUN pip install --no-cache-dir harbor-rewardkit==0.2.4

WORKDIR /app
COPY . /tests/

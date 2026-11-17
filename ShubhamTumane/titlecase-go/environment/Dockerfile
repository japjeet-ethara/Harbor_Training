FROM golang:1.23

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir --break-system-packages uv

WORKDIR /workspace/repo
COPY python-titlecase/ /workspace/repo/
RUN rm -rf /workspace/repo/.git

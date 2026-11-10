FROM golang:1.22-bookworm

# Install base python runtime
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-venv \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install modern pytest compatible with ctrf
RUN pip install --no-cache-dir --break-system-packages "pytest>=8.0.0" "pytest-json-ctrf==0.3.5"

WORKDIR /workspace/repo
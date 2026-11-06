FROM golang:1.23

# Install Python for the original titlecase (used during test generation only)
RUN apt-get update && apt-get install -y python3 python3-pip && \
    pip3 install --break-system-packages titlecase && \
    rm -rf /var/lib/apt/lists/*

# Copy the python-titlecase repo (without .git)
COPY python-titlecase /workspace/repo

WORKDIR /workspace/repo

FROM golang:1.23

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-minimal \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace/repo

COPY . /tests/
RUN chmod +x /tests/test.sh

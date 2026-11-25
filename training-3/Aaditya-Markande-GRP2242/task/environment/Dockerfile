FROM golang:1.23
RUN apt-get update && apt-get install -y --no-install-recommends python3 python3-regex \
    && rm -rf /var/lib/apt/lists/*
COPY python-titlecase /workspace/repo
WORKDIR /workspace/repo

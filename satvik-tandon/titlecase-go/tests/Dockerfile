FROM golang:1.23

RUN apt-get update && apt-get install -y --no-install-recommends python3 && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace/repo

COPY . /tests/

# The examiner's room: separate from the agent's container.
# It gets the agent's /workspace/repo re-materialised as a task artifact.
FROM golang:1.23.9-bookworm

RUN apt-get update \
 && apt-get install -y --no-install-recommends python3 python3-pip \
 && pip3 install --no-cache-dir --break-system-packages "harbor-rewardkit==0.2.4" \
 && rm -rf /var/lib/apt/lists/*

ENV GOTOOLCHAIN=local \
    GOFLAGS=-buildvcs=false \
    GOPROXY=off

WORKDIR /app
COPY . /tests/

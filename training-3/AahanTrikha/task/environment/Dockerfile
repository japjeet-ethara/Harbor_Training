FROM golang:1.23

RUN apt-get update \
 && apt-get install -y --no-install-recommends python3 python3-pip \
 && python3 -m pip install --break-system-packages regex \
 && rm -rf /var/lib/apt/lists/*

COPY repo/ /workspace/repo/
WORKDIR /workspace/repo
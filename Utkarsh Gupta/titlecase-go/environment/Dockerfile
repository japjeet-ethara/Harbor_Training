FROM golang:1.23

# python3 is only needed so the agent (and the verifier) can run the original for comparison
RUN apt-get update \
 && apt-get install -y --no-install-recommends python3 \
 && rm -rf /var/lib/apt/lists/*

# python-titlecase is placed here by ../../setup_repo.sh (no .git folder)
COPY python-titlecase /workspace/repo

WORKDIR /workspace/repo

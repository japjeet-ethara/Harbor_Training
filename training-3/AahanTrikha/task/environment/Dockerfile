FROM golang:1.23

# The base image ships python3; remove every Python runtime so the port cannot
# be delegated to a hidden interpreter at grading time.
RUN apt-get update \
  && apt-get purge -y --auto-remove \
       python3 python3-minimal python3.11 python3.11-minimal \
       libpython3-stdlib libpython3.11-minimal libpython3.11-stdlib \
  && rm -rf /var/lib/apt/lists/*

COPY repo/ /workspace/repo/
WORKDIR /workspace/repo

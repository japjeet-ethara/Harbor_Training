# Pinned Go toolchain (golang:1.23 line) so the agent always gets the same room.
FROM golang:1.23.4-bookworm

# Fail loudly instead of trying to download a newer toolchain (no network for the agent).
ENV GOTOOLCHAIN=local \
    GOFLAGS=-buildvcs=false

# The Python project to port, copied without its .git folder.
COPY python-titlecase /workspace/repo

# Non-root user for the agent so it cannot tamper with root-owned files.
RUN useradd --create-home --uid 1000 agent \
    && chown -R agent:agent /workspace

WORKDIR /workspace/repo

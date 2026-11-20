# golang:1.23 (Debian bookworm), pinned by digest so every trial starts from the same image.
FROM golang@sha256:60deed95d3888cc5e4d9ff8a10c54e5edc008c6ae3fba6187be6fb592e19e8c0

# No interpreter or network helper is installed in the agent image. The Go port must
# compute titlecase on its own from the bundled source and tests.

# The Go toolchain works offline and with the standard library only. Its caches live under
# /tmp so that `go build` works for any user.
ENV GOTOOLCHAIN=local GOPROXY=off GOFLAGS=-mod=mod CGO_ENABLED=0
ENV GOCACHE=/tmp/go-build GOMODCACHE=/tmp/go-mod GOPATH=/tmp/go

# The agent works as this unprivileged user (task.toml [agent] user = "agent").
RUN useradd --create-home --shell /bin/bash agent

# Snapshot of python-titlecase 2.4.1 (commit 42f43e2), taken with `git archive`, so no .git folder.
COPY --chown=agent:agent python-titlecase/ /workspace/repo/

WORKDIR /workspace/repo

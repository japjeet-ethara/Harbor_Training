# Verifier image. Same Go toolchain as the agent image so the build check sees the same compiler.
FROM golang@sha256:60deed95d3888cc5e4d9ff8a10c54e5edc008c6ae3fba6187be6fb592e19e8c0

# grade.py is plain Python 3 with no third-party packages. There is deliberately
# no `regex` package and no copy of python-titlecase here: the submitted program
# cannot find a Python interpreter with the original library to call.
RUN apt-get update \
    && apt-get install -y --no-install-recommends python3 \
    && rm -rf /var/lib/apt/lists/*

ENV GOTOOLCHAIN=local GOPROXY=off GOFLAGS=-mod=mod CGO_ENABLED=0

COPY . /tests/

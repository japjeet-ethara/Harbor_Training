FROM golang:1.23

# Reward Kit needs Python 3.12 or newer. golang:1.23 ships 3.11.
COPY --from=ghcr.io/astral-sh/uv:0.9.7 /uv /usr/local/bin/uv
ENV UV_PYTHON_INSTALL_DIR=/opt/uv-python \
    UV_TOOL_DIR=/opt/uv-tools \
    UV_TOOL_BIN_DIR=/usr/local/bin
RUN uv tool install --python 3.12 harbor-rewardkit==0.2.4

# No cgo, no toolchain downloads and no module downloads while grading.
ENV CGO_ENABLED=0 \
    GOTOOLCHAIN=local \
    GOPROXY=off \
    GOFLAGS=-buildvcs=false
RUN go build std

WORKDIR /workspace/repo

COPY . /tests/

# The agent's program runs as nobody and must not be able to read the answers.
RUN chmod -R go-rwx /tests/data

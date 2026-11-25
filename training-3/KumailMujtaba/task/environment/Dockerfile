FROM golang:1.23

# Pinned upstream snapshot. Cloning rather than copying keeps tests/ and solution/
# out of the agent image, and Harbor's build context is this directory anyway.
RUN git clone https://github.com/ppannuto/python-titlecase /workspace/repo \
    && git -C /workspace/repo checkout 42f43e2de55bf003b286c6f8e8d8b2d26676a167 \
    && rm -rf /workspace/repo/.git

WORKDIR /workspace/repo

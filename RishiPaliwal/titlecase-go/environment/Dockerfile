FROM golang:1.23

ADD https://codeload.github.com/ppannuto/python-titlecase/tar.gz/42f43e2de55bf003b286c6f8e8d8b2d26676a167 /tmp/python-titlecase.tar.gz

RUN mkdir -p /workspace/repo \
    && tar -xzf /tmp/python-titlecase.tar.gz --strip-components=1 -C /workspace/repo \
    && rm /tmp/python-titlecase.tar.gz

WORKDIR /workspace/repo
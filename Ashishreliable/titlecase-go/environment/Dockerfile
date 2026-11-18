FROM golang:1.23

# The build context is ../python-titlecase. Docker cannot COPY a parent path.
COPY . /workspace/repo
RUN rm -rf /workspace/repo/.git

WORKDIR /workspace/repo

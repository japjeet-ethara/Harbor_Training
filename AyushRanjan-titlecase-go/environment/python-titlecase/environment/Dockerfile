FROM golang:1.23

# Build context is the parent of this task, so this is ../python-titlecase
# relative to environment/. Drop VCS metadata after the copy.
COPY python-titlecase/ /workspace/repo/
RUN rm -rf /workspace/repo/.git

WORKDIR /workspace/repo

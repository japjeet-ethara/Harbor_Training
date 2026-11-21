FROM golang:1.23

# Build context is environment/. The Python tree must already be at
# ./python-titlecase, with .git left out of that copy.
COPY python-titlecase/ /workspace/repo/

WORKDIR /workspace/repo

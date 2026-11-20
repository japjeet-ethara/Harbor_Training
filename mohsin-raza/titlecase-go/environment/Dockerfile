FROM golang:1.23

# The original Python project, without its .git folder, is the starting point.
# (Build context is this environment/ folder; python-titlecase/ was copied here from ../python-titlecase.)
COPY python-titlecase /workspace/repo

WORKDIR /workspace/repo

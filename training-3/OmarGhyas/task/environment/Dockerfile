FROM golang:1.23
WORKDIR /workspace/repo
COPY --exclude=.git python-titlecase /workspace/repo
COPY titlecase-go/tests/data/visible.jsonl /workspace/repo/visible.jsonl

#!/bin/bash
set -euo pipefail

mkdir -p /workspace/repo

cp /opt/python-titlecase/go.mod /workspace/repo/go.mod
cp /opt/python-titlecase/main.go /workspace/repo/main.go
cp /opt/python-titlecase/titlecase.go /workspace/repo/titlecase.go

find /workspace/repo -name '*.py' -type f -delete

cd /workspace/repo
go test ./...
go build ./...
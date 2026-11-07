#!/bin/bash
set -euo pipefail

cd /workspace/repo

cp /solution/main.go ./main.go
cp /solution/go.mod ./go.mod

find . -type f -name "*.py" -delete

gofmt -w main.go
go build ./...

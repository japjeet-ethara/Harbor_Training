#!/bin/sh
set -eu
cd /workspace/repo
cp /solution/go.mod /solution/main.go ./
find /workspace/repo -type f -name '*.py' -delete
rm -rf /workspace/repo/titlecase
go build ./...

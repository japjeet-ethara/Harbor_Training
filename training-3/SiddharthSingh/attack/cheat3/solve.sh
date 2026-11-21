#!/bin/sh
set -eu

cp /solution/go.mod /workspace/repo/go.mod
cp /solution/main.go /workspace/repo/main.go
find /workspace/repo -type f -name '*.py' -delete

#!/bin/sh
set -eu

cp /solution/go.mod /workspace/repo/go.mod
cp /solution/main.go /workspace/repo/main.go
cp /solution/lookup.json /workspace/repo/lookup.json
find /workspace/repo -type f -name '*.py' -delete

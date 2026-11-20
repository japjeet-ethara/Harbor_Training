#!/bin/bash
# Oracle: install the reference Go port. The Go code lives in /solution/go, which Harbor uploads only
# for oracle runs; it is never part of the agent's image.
set -euo pipefail
cd /workspace/repo

cp /solution/go/go.mod /solution/go/main.go /solution/go/titlecase.go /solution/go/titlecase_test.go .
find /workspace/repo -name '*.py' -type f -delete
# Deleting the .py files leaves an empty titlecase/ folder; `go build ./...` would then try to
# write its binary to that name and fail ("build output titlecase already exists and is a directory").
find /workspace/repo -mindepth 1 -type d -empty -delete

go test ./...
go build ./...

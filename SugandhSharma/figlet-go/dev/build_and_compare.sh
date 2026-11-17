#!/bin/bash
# Builds the reference solution inside the room image the way solve.sh does, then compares it with the
# frozen answers. Mount the task folder at /task (read only). Usage: bash /task/dev/build_and_compare.sh [FILE.jsonl ...]
set -e
rm -rf /tmp/w && mkdir -p /tmp/w/fonts
cp /task/solution/go.mod /task/solution/*.go /tmp/w/
cp /workspace/repo/pyfiglet/fonts/*.flf /tmp/w/fonts/
cd /tmp/w && gofmt -l . && go vet . && go build -o /tmp/figlet .
cp /task/dev/compare.go /tmp/compare.go
status=0
for cases in "${@:-/task/tests/data/visible.jsonl /task/tests/data/hidden.jsonl}"; do
  for one in $cases; do
    echo "== $one"
    (cd /tmp && go run /tmp/compare.go "$one") || status=1
  done
done
exit $status

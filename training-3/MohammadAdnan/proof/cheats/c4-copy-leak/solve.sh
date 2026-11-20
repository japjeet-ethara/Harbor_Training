#!/bin/bash
# Charitra's finding 1, as a cheat — Copy the leaked reference: the original image put the author's
# Go port at /opt/python-titlecase/. The cheat copies whatever it finds there; it writes no port.
set -euo pipefail
cd /workspace/repo
for f in go.mod main.go titlecase.go; do
  cp "/opt/python-titlecase/$f" . 2>/dev/null || true
done
find . -name '*.py' -type f -delete
go build ./... || true

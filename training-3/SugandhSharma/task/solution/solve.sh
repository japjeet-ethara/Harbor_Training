#!/bin/bash
# Reference solution. The Go port lives next to this script (go.mod and the .go files).
# This script puts it into the repository and removes the Python code.
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
cd /workspace/repo
cp "$here"/go.mod "$here"/*.go .
find . -name '*.py' -delete
find . -name '__pycache__' -type d -prune -exec rm -rf {} +
# The empty folder "titlecase" must go: with a module named titlecase, "go build ./..." would fail with
# 'build output "titlecase" already exists and is a directory'.
find . -type d -empty -delete

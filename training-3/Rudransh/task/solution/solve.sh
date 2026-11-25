#!/bin/bash
set -eu
cd /workspace/repo
cp /solution/go.mod /solution/main.go ./
find /workspace/repo -name '*.py' -type f -delete

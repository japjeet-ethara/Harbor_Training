#!/usr/bin/env bash
set -euo pipefail

solution_dir=$(cd -- "$(dirname -- "$0")" && pwd)
cd /workspace/repo
cp -- "$solution_dir"/go/*.go "$solution_dir"/go/go.mod .
find . -name '*.py' \( -type f -o -type l \) -delete

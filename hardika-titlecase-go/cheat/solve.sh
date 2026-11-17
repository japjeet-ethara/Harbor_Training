#!/usr/bin/env bash
set -euo pipefail

solution_dir=$(cd -- "$(dirname -- "$0")" && pwd)
cd /workspace/repo
cp -- "$solution_dir"/replay/main.go "$solution_dir"/replay/go.mod \
    "$solution_dir/visible-answers.txt" .

#!/usr/bin/env bash
set -euo pipefail

root=$(cd -- "$(dirname -- "$0")/.." && pwd)
output=$(mktemp -d "${TMPDIR:-/tmp}/titlecase-validation.XXXXXXXX")
mkdir -p "$output/go"
cp -- "$root"/solution/go/*.go "$root"/solution/go/go.mod "$output/go/"
export PYTHONDONTWRITEBYTECODE=1 PYTHONUTF8=1 GOTOOLCHAIN=local GOPROXY=off GOSUMDB=off
go=$(command -v go)
python=$(command -v python)
{
    set -x
    "$go" version
    "$python" -VV
    "$python" -c 'import importlib.metadata; print(importlib.metadata.version("regex"))'
    cd "$output/go"
    "$go" build ./...
    "$go" build -o "$output/titlecase" .
    "$python" "$root/tests/gen.py" --output "$output/dataset-1"
    "$python" "$root/tests/gen.py" --output "$output/dataset-2"
    diff -r "$output/dataset-1" "$output/dataset-2"
    diff -r "$output/dataset-1" "$root/tests/data"
    "$python" "$root/tools/unicode_tables.py" --output "$output/unicode_data.go"
    cmp "$output/unicode_data.go" "$root/solution/go/unicode_data.go"
    "$python" "$root/tools/verify_reference.py" "$output/titlecase"
    "$python" "$root/tools/stress.py" "$output/titlecase" 120000
    "$python" "$root/tools/check_protocol.py" "$output/titlecase"
    "$python" "$root/tools/check_grader.py" "$go"
} 2>&1 | tee "$output/validation.log"
printf 'Independent verification logs in %s\n' "$output"

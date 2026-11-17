#!/bin/bash
# usage: bash scripts/diff_check.sh [visible|hidden]
cd /workspaces/titlecase-go
docker run --rm -v "$PWD/solution/solve.sh:/solve.sh:ro" -v "$PWD/tests:/tests:ro" -v "$PWD/scripts:/scripts:ro" \
  titlecase-go-env bash -c "bash /solve.sh && go build -o /tmp/tc_bin . && python3 /scripts/diff.py ${1:-visible}"
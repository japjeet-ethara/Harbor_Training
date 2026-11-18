#!/bin/bash
set -uo pipefail

mkdir -p /logs/verifier
printf '{"reward":0,"build":0,"no_python":0,"behaviour":0}\n' > /logs/verifier/reward.json

if ! command -v go >/dev/null 2>&1; then
  echo "Go is unavailable in the verifier environment; leaving zero reward." >&2
  exit 0
fi

cd /tests || exit 0
go run grade.go
grader_status=$?
if [ "$grader_status" -ne 0 ]; then
  echo "Go grader exited with status $grader_status; leaving fallback reward if no report was written." >&2
fi
exit 0

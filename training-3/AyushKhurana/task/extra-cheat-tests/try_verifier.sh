#!/bin/bash
# Runs the task's real grader on fake workspaces, without Harbor, to prove the checks work.
set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
TASK="$HERE/../titlecase-go"
echo "building grader image..."
docker build -q -t titlecase-go-verifier "$TASK/tests" >/dev/null || { echo "BUILD FAILED"; exit 1; }
run() {   # run <label> <workspace folder>
  local w out; w=$(mktemp -d); out=$(mktemp -d); cp -r "$2/." "$w/"
  docker run --rm --network none -v "$w:/workspace/repo" -v "$out:/logs/verifier" \
    titlecase-go-verifier bash /tests/test.sh > "$out/log.txt" 2>&1 || echo "  ($1: verifier exited non-zero, see $out/log.txt)"
  printf '%-10s %s\n' "$1" "$(tr -d '\n ' < "$out/reward.json" 2>/dev/null || echo NO-REWARD-FILE)"
}
run nop       "$TASK/environment/repo"
for ws in buildonly echo peek exec; do run "$ws" "$HERE/workspaces/$ws"; done

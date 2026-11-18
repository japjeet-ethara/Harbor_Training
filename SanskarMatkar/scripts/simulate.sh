#!/bin/bash
# Local stand-in for a Harbor trial when Docker images can't be pulled:
# same scripts, same in-container paths (/workspace/repo, /solution, /tests, /logs).
#   scripts/simulate.sh oracle | nop | cheat
set -euo pipefail
MODE=${1:?oracle|nop|cheat}
TASK=$(cd "$(dirname "$0")/.." && pwd)
export GOTOOLCHAIN=local GOPROXY=off GOFLAGS=-mod=readonly CGO_ENABLED=0

# 1. fresh agent workspace (what environment/Dockerfile builds)
rm -rf /workspace/repo /solution /tests /logs/verifier
mkdir -p /workspace && cp -a "$TASK/environment/python-titlecase" /workspace/repo

# 2. agent phase
case "$MODE" in
  oracle) cp -a "$TASK/solution" /solution; (cd /workspace/repo && bash /solution/solve.sh) ;;
  cheat)  mkdir -p /solution && cp "$TASK/cheat/solve.sh" /solution/solve.sh; (cd /workspace/repo && bash /solution/solve.sh) ;;
  nop)    : ;;
esac
rm -rf /solution   # the verifier never sees the solution

# 3. separate verifier: only /workspace/repo (artifact) + /tests
cp -a "$TASK/tests" /tests
mkdir -p /logs/verifier
bash /tests/test.sh >/tmp/verifier-$MODE.log 2>&1 || true
echo "== $MODE"; python3 -c "import json;print(json.load(open('/logs/verifier/reward.json')))"

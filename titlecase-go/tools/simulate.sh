#!/bin/bash
# Reproduce one Harbor trial WITHOUT Docker (for authors with no Docker daemon).
#   tools/simulate.sh oracle|nop|cheat
# Rebuilds the agent container's filesystem (/workspace/repo from the image
# recipe), runs the chosen "agent", then runs the unmodified verifier
# (tests/test.sh) exactly as Harbor would, and prints reward.json.
set -euo pipefail
MODE="${1:?oracle|nop|cheat}"
TASK="$(cd "$(dirname "$0")/.." && pwd)"
export PATH="${GO_BIN:-/opt/go123/go/bin}:$PATH"
export GOTOOLCHAIN=local GOFLAGS=-buildvcs=false GOPROXY=off   # = Dockerfile ENV

rm -rf /workspace /solution /tests /logs
mkdir -p /workspace /logs/verifier
cp -r "$TASK/environment/python-titlecase" /workspace/repo      # = Dockerfile COPY

case "$MODE" in
  oracle) cp -r "$TASK/solution" /solution; (cd /workspace/repo && bash /solution/solve.sh >/tmp/agent.log 2>&1) || { cat /tmp/agent.log; exit 1; } ;;
  cheat)  mkdir /solution; cp "$TASK/cheat/solve.sh" /solution/solve.sh; (cd /workspace/repo && bash /solution/solve.sh >/tmp/agent.log 2>&1) || { cat /tmp/agent.log; exit 1; } ;;
  nop)    : ;;                                                   # does nothing
  *) echo "unknown mode"; exit 2 ;;
esac

cp -r "$TASK/tests" /tests                                       # = tests/Dockerfile COPY
bash /tests/test.sh
echo "== $MODE =="; cat /logs/verifier/reward.json; echo

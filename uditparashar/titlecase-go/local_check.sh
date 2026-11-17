#!/bin/bash
# Local stand-in for `harbor run -a <oracle|nop|cheat>` when Docker is not available.
# Mimics Harbor: /workspace/repo (from environment/), /tests, /logs; solution is run from the
# container WORKDIR (/workspace/repo); then tests/test.sh runs and writes /logs/verifier/reward.json.
# Usage: local_check.sh <task-dir> <oracle|nop|cheat|cheat_nopy>
set -uo pipefail
TASK=$(readlink -f "$1"); MODE=$2
rm -rf /workspace /tests /logs /solution
mkdir -p /workspace /logs/verifier /logs/agent
cp -r "$TASK/environment/python-titlecase" /workspace/repo
cp -r "$TASK/tests" /tests
rm -rf /tests/Dockerfile.bak
cd /workspace/repo
case "$MODE" in
  oracle)      cp -r "$TASK/solution" /solution; bash /solution/solve.sh ;;
  nop)         : ;;
  cheat)       bash "$TASK/cheat/solve.sh" ;;
  cheat_nopy)  bash "$TASK/cheat/solve.sh"; find /workspace/repo -name '*.py' -type f -delete ;;
  *) echo "bad mode"; exit 2 ;;
esac >/logs/agent/solve.log 2>&1
echo "solution step exit code: $?"
cd /workspace/repo
bash /tests/test.sh
echo "test.sh exit code: $?"
echo "--- /logs/verifier/reward.json ---"; cat /logs/verifier/reward.json 2>/dev/null || echo "(no reward file!)"; echo

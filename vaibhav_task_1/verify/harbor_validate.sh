#!/bin/bash
# Real Harbor validation (Steps 2, 6 and 7) — run on a machine with Docker and
# Harbor installed (e.g. `uv tool install harbor`). Prints the three rewards.
#
#   verify/harbor_validate.sh            # docker build check + oracle + nop + cheat
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
JOBS="$ROOT/jobs"
mkdir -p "$JOBS"

echo "== Step 2: image builds and contains the Python code =="
docker build -t titlecase-go-env titlecase-go/environment
docker run --rm titlecase-go-env ls /workspace/repo /workspace/repo/titlecase

echo "== Lint =="
harbor check -p ./titlecase-go || harbor lint -p ./titlecase-go || echo "(lint/check not available in this Harbor version)"

echo "== Step 6: oracle (must be 1.0) =="
harbor run -p ./titlecase-go -a oracle -o "$JOBS" --job-name oracle

echo "== Step 7a: nop (must be 0.0) =="
harbor run -p ./titlecase-go -a nop -o "$JOBS" --job-name nop

echo "== Step 7b: cheat (must be < 0.2) =="
cp titlecase-go/solution/solve.sh titlecase-go/solution/solve.sh.bak
trap 'mv -f titlecase-go/solution/solve.sh.bak titlecase-go/solution/solve.sh' EXIT
cp titlecase-go/cheat/solve.sh titlecase-go/solution/solve.sh
harbor run -p ./titlecase-go -a oracle -o "$JOBS" --job-name cheat
mv -f titlecase-go/solution/solve.sh.bak titlecase-go/solution/solve.sh
trap - EXIT

python3 - "$JOBS" <<'PY'
import json, pathlib, sys
jobs = pathlib.Path(sys.argv[1])
for name in ("oracle", "nop", "cheat"):
    files = sorted((jobs / name).glob("*/verifier/reward.json")) or sorted((jobs / name).glob("*/verifier/reward.txt"))
    for f in files:
        print(f"{name:<7} {f.relative_to(jobs)}: {f.read_text().strip()}")
PY
echo "Open the viewer with: harbor view $JOBS"

#!/bin/bash
# Local, Docker-free replay of the Harbor validation runs for titlecase-go.
#
# For each "agent" it mimics one Harbor trial:
#   1. fresh workspace = copy of environment/python-titlecase  (the Docker COPY)
#   2. run the agent against it                                (solve.sh / nothing / cheat)
#   3. copy tests/ to a SEPARATE dir (the agent never saw it)  (environment_mode = separate)
#   4. run the real tests/test.sh -> reward.json               (same verifier script)
#
# Needs: bash, Go >= 1.23, Python >= 3.11. No network, no Docker.
# By default test.sh is pointed at verify/rewardkit_shim (offline stand-in).
# Set USE_REAL_REWARDKIT=1 to let test.sh download harbor-rewardkit with uvx.
#
# Usage: verify/run_local.sh            # oracle, nop, cheat (+ extra baselines)
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TASK="$ROOT/titlecase-go"
OUT="$ROOT/results"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
mkdir -p "$OUT"

command -v go >/dev/null || { echo "Go is required (go 1.23+)"; exit 2; }
python3 -c 'import sys; assert sys.version_info >= (3, 11)' || { echo "Python 3.11+ required"; exit 2; }

if [ "${USE_REAL_REWARDKIT:-0}" = "1" ]; then
  RK_CMD=""
  echo "Using the real harbor-rewardkit via uvx (needs network)"
else
  RK_CMD="python3 -m rewardkit"
  echo "Using the offline Reward Kit shim (verify/rewardkit_shim)"
fi

# ---------------------------------------------------------------- agents
agent_oracle()   { REPO="$1" bash "$TASK/solution/solve.sh" >/dev/null; }
agent_nop()      { :; }
agent_cheat()    { REPO="$1" bash "$TASK/cheat/solve.sh" >/dev/null; }
# Extra baselines (not required by the task, shown for information):
agent_build_only() {   # a Go program that builds but does nothing; .py files left
  printf 'module titlecase-go\n\ngo 1.23\n' > "$1/go.mod"
  printf 'package main\n\nfunc main() {}\n' > "$1/main.go"
}
agent_cheat_rm_py() {  # the cheat, plus deleting the .py files
  agent_cheat "$1"; find "$1" -name '*.py' -delete
}
agent_read_hidden() {  # at RUN time, hunt for hidden_expected.txt on disk and print it
  printf 'module titlecase-go\n\ngo 1.23\n' > "$1/go.mod"
  cat > "$1/main.go" <<'EOF'
package main

import (
	"io/fs"
	"os"
	"path/filepath"
)

func main() {
	for _, root := range []string{"/tests", os.TempDir(), "/tmp"} {
		filepath.WalkDir(root, func(p string, d fs.DirEntry, err error) error {
			if err == nil && !d.IsDir() && d.Name() == "hidden_expected.txt" {
				if b, e := os.ReadFile(p); e == nil {
					os.Stdout.Write(b)
					os.Exit(0)
				}
			}
			return nil
		})
	}
}
EOF
  find "$1" -name '*.py' -delete
}
agent_identity() {     # echo every line unchanged, .py deleted
  printf 'module titlecase-go\n\ngo 1.23\n' > "$1/go.mod"
  cat > "$1/main.go" <<'EOF'
package main

import (
	"io"
	"os"
)

func main() { io.Copy(os.Stdout, os.Stdin) }
EOF
  find "$1" -name '*.py' -delete
}

run_trial() {
  local name="$1" fn="$2"
  local t="$WORK/$name"
  mkdir -p "$t/workspace" "$t/tests" "$t/logs/verifier"
  cp -r "$TASK/environment/python-titlecase" "$t/workspace/repo"
  "$fn" "$t/workspace/repo"
  cp -r "$TASK/tests/." "$t/tests/"
  TESTS_DIR="$t/tests" WORKSPACE="$t/workspace/repo" LOGS_DIR="$t/logs/verifier" \
    REWARDKIT_CMD="$RK_CMD" PYTHONPATH="$ROOT/verify/rewardkit_shim" \
    bash "$t/tests/test.sh" >"$t/verifier.log" 2>&1 || { cat "$t/verifier.log"; echo "verifier error for $name"; exit 1; }
  mkdir -p "$OUT/$name"
  cp "$t/logs/verifier/reward.json" "$t/logs/verifier/reward-details.json" "$OUT/$name/"
  python3 - "$name" "$t/logs/verifier/reward.json" <<'EOF'
import json, sys
r = json.load(open(sys.argv[2]))
print(f"{sys.argv[1]:<12} reward={r['reward']:.4f}   build={r.get('build', 0):.0f}  "
      f"no_python={r.get('no_python', 0):.0f}  behaviour={r.get('behaviour', 0):.4f}")
EOF
}

echo
echo "== Step 4 checks: answer sheets come from the original code and are deterministic =="
for i in 1 2; do
  mkdir -p "$WORK/gen$i"
  cp -r "$TASK/tests" "$WORK/gen$i/tests"
  python3 "$WORK/gen$i/tests/gen.py" --repo "$ROOT/python-titlecase" >/dev/null
done
diff -r "$WORK/gen1/tests/data" "$WORK/gen2/tests/data" >/dev/null && echo "two regenerations identical: yes"
diff -r "$WORK/gen1/tests/data" "$TASK/tests/data" >/dev/null && echo "committed data == regenerated data: yes"
python3 - "$TASK/tests/data" "$ROOT/python-titlecase" <<'EOF'
import os, sys
d, repo = sys.argv[1], sys.argv[2]
n = {f: open(os.path.join(d, f), encoding="utf-8").read().count("\n") for f in sorted(os.listdir(d))}
print("line counts:", n)
assert n["inputs.txt"] == n["expected.txt"] and n["hidden_inputs.txt"] == n["hidden_expected.txt"]
vis = set(open(os.path.join(d, "inputs.txt"), encoding="utf-8").read().split("\n")[:-1])
hid = open(os.path.join(d, "hidden_inputs.txt"), encoding="utf-8").read().split("\n")[:-1]
print("visible/hidden overlap:", sum(h in vis for h in hid))
sys.modules["regex"] = None
sys.path.insert(0, repo)
from titlecase import titlecase
ins = open(os.path.join(d, "inputs.txt"), encoding="utf-8").read().split("\n")[:-1]
exp = open(os.path.join(d, "expected.txt"), encoding="utf-8").read().split("\n")[:-1]
for i in (0, 7, 123, 999, 1999):
    assert titlecase(ins[i]) == exp[i]
    print(f"  spot-check line {i+1}: {ins[i]!r} -> {exp[i]!r}  ok")
EOF

echo
echo "== Harbor-style validation runs =="
run_trial oracle      agent_oracle
run_trial nop         agent_nop
run_trial cheat       agent_cheat
echo
echo "== Extra baselines (information only) =="
run_trial build_only  agent_build_only
run_trial cheat_rm_py agent_cheat_rm_py
run_trial identity    agent_identity
run_trial read_hidden agent_read_hidden

python3 - "$OUT" <<'EOF'
import json, sys, os
out = sys.argv[1]
r = {n: json.load(open(os.path.join(out, n, "reward.json")))["reward"]
     for n in ("oracle", "nop", "cheat")}
ok = abs(r["oracle"] - 1.0) < 1e-9 and r["nop"] == 0.0 and r["cheat"] < 0.2
print()
print(f"oracle = {r['oracle']:.4f}  (must be 1.0)")
print(f"nop    = {r['nop']:.4f}  (must be 0.0)")
print(f"cheat  = {r['cheat']:.4f}  (must be < 0.2)")
print("RESULT:", "PASS" if ok else "FAIL")
json.dump(r, open(os.path.join(out, "summary.json"), "w"), indent=2)
sys.exit(0 if ok else 1)
EOF

#!/usr/bin/env bash
set -euo pipefail

# Security & environment hardening
export CGO_ENABLED=0
export GOFLAGS=-mod=mod
export GOPROXY=off
export GOTOOLCHAIN=local

# Ensure verifier log dir exists
mkdir -p /logs/verifier

# Run Python evaluator for the 3 checks
python3 - << 'EOF'
import json
import sys
import subprocess
from pathlib import Path

# Try to run build check
build_script = Path("/tests/checks/build/build.py")
no_python_script = Path("/tests/checks/no_python/no_python.py")
behaviour_script = Path("/tests/checks/behaviour/behaviour.py")

def run_check(script_path):
    if not script_path.exists():
        print(f"Script does not exist: {script_path}", file=sys.stderr)
        return 0.0
    try:
        proc = subprocess.run([sys.executable, str(script_path)], capture_output=True, text=True, timeout=120)
        print(f"--- Output of {script_path.name} ---")
        print(f"STDOUT: {proc.stdout.strip()}")
        print(f"STDERR: {proc.stderr.strip()}")
        out = proc.stdout.strip().splitlines()
        if out:
            return float(out[-1])
        return 0.0
    except Exception as e:
        print(f"Error running {script_path}: {e}", file=sys.stderr)
        return 0.0

score_build = run_check(build_script)
score_no_python = run_check(no_python_script)
score_behaviour = run_check(behaviour_script)

# Weighted-mean aggregation: build=1, no_python=1, behaviour=4
total_weight = 1.0 + 1.0 + 4.0
weighted_reward = (score_build * 1.0 + score_no_python * 1.0 + score_behaviour * 4.0) / total_weight

result = {
    "build": score_build,
    "no_python": score_no_python,
    "behaviour": score_behaviour,
    "reward": round(weighted_reward, 6)
}

print(f"Final Verifier Result: {json.dumps(result, indent=2)}")

# Write reward files
Path("/logs/verifier/reward.json").write_text(json.dumps(result, indent=2) + "\n")
Path("/logs/verifier/reward.txt").write_text(f"{result['reward']}\n")

EOF

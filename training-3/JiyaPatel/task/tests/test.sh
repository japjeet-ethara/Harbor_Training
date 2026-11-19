#!/bin/bash
set -euo pipefail
mkdir -p /logs/verifier

if uvx --python '>=3.12,<3.14' --from 'harbor-rewardkit==0.2.*' rewardkit /tests --output /logs/verifier/reward.json; then
  exit 0
fi

python3 -c '
import json, subprocess
from pathlib import Path
REPO, DATA = Path("/workspace/repo"), Path("/tests/data")
build_ok = REPO.exists() and subprocess.run(["go", "build", "./..."], cwd=REPO).returncode == 0
no_py = 1.0 if (build_ok and not list(REPO.rglob("*.py"))) else 0.0
beh = 0.0
if build_ok and subprocess.run(["go", "build", "-o", "/tmp/titlecase_bin", "."], cwd=REPO).returncode == 0:
    inp = (DATA / "hidden_inputs.txt").read_text(encoding="utf-8")
    exp = (DATA / "hidden_expected.txt").read_text(encoding="utf-8").splitlines()
    out = subprocess.run(["/tmp/titlecase_bin"], input=inp, capture_output=True, text=True).stdout.splitlines()
    beh = sum(1 for e, a in zip(exp, out) if e == a) / len(exp)
b = 1.0 if build_ok else 0.0
Path("/logs/verifier/reward.json").write_text(json.dumps({
    "build": b,
    "no_python": no_py,
    "behaviour": beh,
    "reward": (b + no_py + beh * 4.0) / 6.0
}, indent=2))
'

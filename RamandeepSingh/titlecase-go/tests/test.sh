#!/bin/bash
set -eo pipefail

mkdir -p /logs/verifier

WORKSPACE="/workspace/repo"
TESTS_DIR="/tests"

run_fallback_grading() {
    python3 - << 'EOF'
import json
import os
import sys
from pathlib import Path

workspace = Path("/workspace/repo")
tests_dir = Path("/tests")
sys.path.insert(0, str(tests_dir))

from build import check_build
from no_python import check_no_python
from behaviour import check_behaviour

s_build = float(check_build(workspace))
s_no_py = float(check_no_python(workspace))
s_behav = float(check_behaviour(workspace))

# Weighted-mean aggregation: weights { build = 1.0, no_python = 1.0, behaviour = 4.0 }
total_weight = 1.0 + 1.0 + 4.0
w_mean = (1.0 * s_build + 1.0 * s_no_py + 4.0 * s_behav) / total_weight

scores = {
    "reward": round(w_mean, 6),
    "build": round(s_build, 6),
    "no_python": round(s_no_py, 6),
    "behaviour": round(s_behav, 6)
}

os.makedirs("/logs/verifier", exist_ok=True)
with open("/logs/verifier/reward.json", "w") as f:
    json.dump(scores, f, indent=2)

with open("/logs/verifier/reward.txt", "w") as f:
    f.write(f"{scores['reward']}\n")

print(f"Evaluation completed: {scores}")
EOF
}

# Run RewardKit using uvx as configured
echo "Running RewardKit via uvx..."
if uvx --from 'harbor-rewardkit==0.2.*' rewardkit "${TESTS_DIR}" --workspace "${WORKSPACE}" --output /logs/verifier; then
    echo "RewardKit verification succeeded."
else
    echo "RewardKit execution failed; running fallback grading..."
    run_fallback_grading
fi

# Ensure reward.json exists
if [ ! -f /logs/verifier/reward.json ]; then
    run_fallback_grading
fi

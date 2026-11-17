#!/bin/bash
set -euo pipefail

mkdir -p /logs/verifier

# Run RewardKit against /tests
if command -v rewardkit >/dev/null 2>&1; then
    rewardkit /tests --workspace /workspace/repo || true
elif command -v uvx >/dev/null 2>&1; then
    uvx --python '>=3.12,<3.14' --from 'harbor-rewardkit==0.2.*' rewardkit /tests --workspace /workspace/repo || true
fi

# Fallback in case rewardkit CLI did not generate /logs/verifier/reward.json
if [ ! -f /logs/verifier/reward.json ]; then
    python3 - << 'EOF'
import json
import sys
from pathlib import Path

sys.path.insert(0, "/tests")
sys.path.insert(0, str(Path(__file__).resolve().parent))

try:
    from build import build
    score_build = float(build(Path("/workspace/repo")))
except Exception as e:
    score_build = 0.0

try:
    from no_python import no_python
    score_no_python = float(no_python(Path("/workspace/repo")))
except Exception as e:
    score_no_python = 0.0

try:
    from behaviour import behaviour
    score_behaviour = float(behaviour(Path("/workspace/repo")))
except Exception as e:
    score_behaviour = 0.0

# Weighted-mean aggregation: weights build=1, no_python=1, behaviour=4
total_weight = 1.0 + 1.0 + 4.0
reward = (1.0 * score_build + 1.0 * score_no_python + 4.0 * score_behaviour) / total_weight

output_data = {
    "build": score_build,
    "no_python": score_no_python,
    "behaviour": score_behaviour,
    "reward": reward,
}

logs_dir = Path("/logs/verifier")
logs_dir.mkdir(parents=True, exist_ok=True)

with open(logs_dir / "reward.json", "w") as f:
    json.dump(output_data, f, indent=2)

with open(logs_dir / "reward.txt", "w") as f:
    f.write(f"{reward}\n")

print(f"Verifier written to /logs/verifier/reward.json: {output_data}")
EOF
fi

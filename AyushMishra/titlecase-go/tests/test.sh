#!/bin/bash
set -eo pipefail

mkdir -p /logs/verifier

# The generated test data is checked in; this helper imports an unavailable
# source package and is not part of the verifier tests.
rm -f /tests/gen.py

# Run RewardKit against the verifier tests and workspace.
uvx --from 'harbor-rewardkit==0.2.*' rewardkit /tests --workspace /workspace/repo --output /logs/verifier/reward.json

# Ensure /logs/verifier/reward.json exists and is valid
if [ ! -f /logs/verifier/reward.json ]; then
  echo "Generating reward.json from rewardkit execution..."
  python3 -c "
import json
from pathlib import Path
import rewardkit

# Fallback evaluation if rewardkit CLI output location differs
from tests.build import check_build
from tests.no_python import check_no_python
from tests.behaviour import check_behaviour

ws = Path('/workspace/repo')
s_build = float(check_build(ws))
s_no_python = float(check_no_python(ws))
s_behaviour = float(check_behaviour(ws))
final_reward = (1.0 * s_build + 1.0 * s_no_python + 4.0 * s_behaviour) / 6.0

out = {
    'build': s_build,
    'no_python': s_no_python,
    'behaviour': s_behaviour,
    'reward': round(final_reward, 4)
}

with open('/logs/verifier/reward.json', 'w') as f:
    json.dump(out, f, indent=2)
"
fi

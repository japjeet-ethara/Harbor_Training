#!/bin/bash
set -euo pipefail

reward=/logs/verifier/reward.json
rewardkit /tests --workspace /workspace/repo --output "$reward"

python - "$reward" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
scores = json.loads(path.read_text(encoding="utf-8"))
if scores["build"] != 1.0 or scores["no_python"] != 1.0 or scores["behaviour"] < 0.90:
    scores["reward"] = 0.0
path.write_text(json.dumps(scores, indent=2) + "\n", encoding="utf-8")
PY

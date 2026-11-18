#!/bin/bash
set -euo pipefail
mkdir -p /logs/verifier

# Run debug script to stderr only (won't interfere with JSON)
python3 /tests/debug_diff.py >&2 || true

# Run rewardkit and save JSON properly
uvx --python '>=3.12,<3.14' --from 'harbor-rewardkit==0.2.*' rewardkit /tests > /logs/verifier/reward.json

#!/bin/bash
# Runs Reward Kit over /tests/checks (build.py, no_python.py, behaviour.py + reward.toml)
# against the agent's work in /workspace/repo and writes /logs/verifier/reward.json.
set -uo pipefail

mkdir -p /logs/verifier
rm -f /logs/verifier/reward.txt /logs/verifier/reward.json /logs/verifier/reward-details.json

# Reward Kit writes into a root-only folder (mktemp -d is mode 0700). The agent's program
# runs during grading, so nothing it could leave in /logs/verifier may count as a score.
out="$(mktemp -d)"
/opt/rk/bin/python -m rewardkit /tests/checks --workspace /workspace/repo --output "$out/reward.json"
status=$?

rm -f /logs/verifier/reward.txt /logs/verifier/reward.json /logs/verifier/reward-details.json
if [ "$status" -eq 0 ] && [ -s "$out/reward.json" ]; then
    cp "$out/reward.json" /logs/verifier/reward.json
    cp "$out/reward-details.json" /logs/verifier/reward-details.json 2>/dev/null || true
fi
rm -rf "$out"

# Reward Kit must have produced a score; otherwise the verifier errors (no silent 0).
test -s /logs/verifier/reward.json

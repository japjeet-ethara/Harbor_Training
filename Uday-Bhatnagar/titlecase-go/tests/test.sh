#!/usr/bin/env bash
#
# Runs the three Reward Kit criteria in /tests against the submitted workspace.
# The verifier image already contains /tests and harbor-rewardkit; no network
# access is needed at verification time.
set -uo pipefail

REWARD_JSON=/logs/verifier/reward.json
mkdir -p /logs/verifier
rm -f "$REWARD_JSON" /logs/verifier/reward.txt

fallback_zero() {
    printf '{"reward": 0.0}\n' > "$REWARD_JSON"
}

if [ ! -d /workspace/repo ]; then
    echo "ERROR: /workspace/repo was not restored into the verifier environment" >&2
    fallback_zero
    exit 1
fi

cd /tests || {
    echo "ERROR: /tests is missing" >&2
    fallback_zero
    exit 1
}

python -m rewardkit /tests/criteria \
    --workspace /workspace/repo \
    --output "$REWARD_JSON" \
    --max-concurrent-programmatic 1
status=$?

if [ "$status" -ne 0 ]; then
    echo "ERROR: rewardkit exited with status $status" >&2
    fallback_zero
    exit 1
fi

if [ ! -s "$REWARD_JSON" ]; then
    echo "ERROR: rewardkit did not write $REWARD_JSON" >&2
    fallback_zero
    exit 1
fi

if ! python - "$REWARD_JSON" <<'PY'
import json
import math
import sys

path = sys.argv[1]
with open(path, encoding="utf-8") as handle:
    data = json.load(handle)
if not isinstance(data, dict) or "reward" not in data:
    raise SystemExit("reward.json has no 'reward' key")
value = data["reward"]
if not isinstance(value, (int, float)) or isinstance(value, bool):
    raise SystemExit(f"reward is not numeric: {value!r}")
if not math.isfinite(float(value)):
    raise SystemExit(f"reward is not finite: {value!r}")
PY
then
    echo "ERROR: reward.json failed validation" >&2
    fallback_zero
    exit 1
fi

echo "reward written to $REWARD_JSON"
cat "$REWARD_JSON"

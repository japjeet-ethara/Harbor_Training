#!/bin/bash
# Verifier entry point. Runs the Reward Kit criteria in /tests against the
# agent's repository and writes /logs/verifier/reward.json with one score per
# check plus the combined score:
#   {"build": ..., "no_python": ..., "behaviour": ..., "reward": ...}
# (Reward Kit's own reward.json only carries the combined key; the per-check
# numbers are taken from its reward-details.json.)
set -uo pipefail

REPO="${TITLECASE_REPO:-/workspace/repo}"
TESTS="${TITLECASE_TESTS_DIR:-/tests}"
OUT="${TITLECASE_REWARD_OUT:-/logs/verifier/reward.json}"
RK="$(mktemp -d)"

mkdir -p "$(dirname "$OUT")"
# The expected answers are for the examiner only: the agent's program is run
# later as an unprivileged user and must not be able to read them.
chmod -R go-rwx "$TESTS" 2>/dev/null || true

rewardkit "$TESTS" --workspace "$REPO" --output "$RK/reward.json" || exit 1

python3 - "$RK" "$OUT" <<'PY'
import json, sys
rk, out = sys.argv[1], sys.argv[2]
main = json.load(open(f"{rk}/reward.json"))
details = json.load(open(f"{rk}/reward-details.json"))
scores = {c["name"]: c["detail"]["score"] for c in details["reward"]["components"]}
scores["reward"] = main["reward"]
json.dump(scores, open(out, "w"), indent=2)
json.dump(details, open(out.replace("reward.json", "reward-details.json"), "w"), indent=2)
PY

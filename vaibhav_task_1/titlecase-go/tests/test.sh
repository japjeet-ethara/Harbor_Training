#!/bin/bash
# Verifier entry point. Runs the Reward Kit criteria in tests/checks/ against
# the agent's workspace and writes /logs/verifier/reward.json
# (build, no_python, behaviour, reward = weighted mean 1:1:4).
#
# Overridable for local runs (verify/run_local.sh sets these):
#   TESTS_DIR      default /tests
#   WORKSPACE      default /workspace/repo
#   LOGS_DIR       default /logs/verifier
#   REWARDKIT_CMD  default: uvx-installed harbor-rewardkit 0.2.*
set -euo pipefail

TESTS_DIR="${TESTS_DIR:-/tests}"
WORKSPACE="${WORKSPACE:-/workspace/repo}"
LOGS_DIR="${LOGS_DIR:-/logs/verifier}"
export TC_TESTS_DIR="$TESTS_DIR"
export PATH="$PATH:/usr/local/go/bin:$HOME/.local/bin"

mkdir -p "$LOGS_DIR"
# Anti-tampering: never trust a reward file that exists before grading.
rm -f "$LOGS_DIR/reward.txt" "$LOGS_DIR/reward.json" "$LOGS_DIR/reward-details.json"

if [ -z "${REWARDKIT_CMD:-}" ]; then
  if ! command -v uvx >/dev/null 2>&1; then
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
  fi
  REWARDKIT_CMD="uvx --python >=3.12,<3.14 --from harbor-rewardkit==0.2.* rewardkit"
fi

set -f  # no globbing of the version spec
# shellcheck disable=SC2086
$REWARDKIT_CMD "$TESTS_DIR/checks" \
  --workspace "$WORKSPACE" \
  --output "$LOGS_DIR/reward.json"

echo "reward.json:"
cat "$LOGS_DIR/reward.json"

#!/bin/bash
set -euo pipefail

DEST_DIR="/logs/verifier"
FINAL_REWARD="$DEST_DIR/reward.json"
FINAL_DETAILS="$DEST_DIR/reward-details.json"

mkdir -p "$DEST_DIR"
# Ensure no stale reward artifacts exist from previous runs
rm -f "$FINAL_REWARD" "$FINAL_DETAILS"

# Create a private temporary directory for raw RewardKit execution
TMP_DIR=$(mktemp -d /tmp/verifier-rk.XXXXXX)
trap 'rm -rf "$TMP_DIR"' EXIT

RAW_REWARD="$TMP_DIR/reward.json"
RAW_DETAILS="$TMP_DIR/reward-details.json"

# Run RewardKit isolated to the private temporary directory
rewardkit /tests/checks --workspace /workspace/repo --output "$RAW_REWARD"

# Validate component scores, preserve diagnostics, and stage gated reward
STAGE_REWARD="$DEST_DIR/.reward.json.tmp"
rm -f "$STAGE_REWARD"

python3 - "$RAW_DETAILS" "$FINAL_DETAILS" "$STAGE_REWARD" <<'EOF'
import json
import math
import sys
from pathlib import Path

raw_details_path = Path(sys.argv[1])
final_details_path = Path(sys.argv[2])
stage_reward_path = Path(sys.argv[3])

if not raw_details_path.is_file():
    print(f"Verifier error: details file {raw_details_path} missing", file=sys.stderr)
    sys.exit(1)

try:
    data = json.loads(raw_details_path.read_text(encoding="utf-8"))
except Exception as e:
    print(f"Verifier error: failed to parse JSON in {raw_details_path}: {e}", file=sys.stderr)
    sys.exit(1)

if not isinstance(data, dict) or "reward" not in data or not isinstance(data["reward"], dict):
    print("Verifier error: top-level 'reward' object missing or invalid", file=sys.stderr)
    sys.exit(1)

components = data["reward"].get("components")
if not isinstance(components, list):
    print("Verifier error: 'components' list missing in reward details", file=sys.stderr)
    sys.exit(1)

seen_names = []
scores = {}

for comp in components:
    if not isinstance(comp, dict):
        print("Verifier error: component entry is not a dict", file=sys.stderr)
        sys.exit(1)
    name = comp.get("name")
    if not isinstance(name, str):
        print("Verifier error: component name is not a string", file=sys.stderr)
        sys.exit(1)
    seen_names.append(name)

    detail = comp.get("detail")
    if not isinstance(detail, dict):
        print(f"Verifier error: component '{name}' missing detail", file=sys.stderr)
        sys.exit(1)

    if name in ("build", "no_python"):
        if "score" not in detail:
            print(f"Verifier error: component '{name}' missing score", file=sys.stderr)
            sys.exit(1)

        score = detail["score"]
        # Require numeric, finite scores, excluding booleans and numeric strings
        if isinstance(score, bool) or not isinstance(score, (int, float)):
            print(f"Verifier error: component '{name}' score {score!r} is not a valid number (booleans/strings excluded)", file=sys.stderr)
            sys.exit(1)

        if not math.isfinite(score):
            print(f"Verifier error: component '{name}' score is not finite", file=sys.stderr)
            sys.exit(1)

        scores[name] = float(score)
    elif name == "behaviour":
        criteria = detail.get("criteria")
        if not isinstance(criteria, list):
            print("Verifier error: 'criteria' list missing in behaviour detail", file=sys.stderr)
            sys.exit(1)

        matching_criteria = []
        for crit in criteria:
            if not isinstance(crit, dict):
                print("Verifier error: criterion entry is not a dict", file=sys.stderr)
                sys.exit(1)
            if crit.get("name") == "hidden_output_matches":
                matching_criteria.append(crit)

        if len(matching_criteria) != 1:
            print(f"Verifier error: behaviour component must have exactly one criterion named 'hidden_output_matches', found {len(matching_criteria)}", file=sys.stderr)
            sys.exit(1)

        crit = matching_criteria[0]
        if "raw" not in crit:
            print("Verifier error: criterion 'hidden_output_matches' missing 'raw' value", file=sys.stderr)
            sys.exit(1)

        raw_val = crit["raw"]
        # Require numeric, finite raw value, excluding booleans and numeric strings
        if isinstance(raw_val, bool) or not isinstance(raw_val, (int, float)):
            print(f"Verifier error: criterion 'hidden_output_matches' raw value {raw_val!r} is not a valid number (booleans/strings excluded)", file=sys.stderr)
            sys.exit(1)

        if not math.isfinite(raw_val):
            print("Verifier error: criterion 'hidden_output_matches' raw value is not finite", file=sys.stderr)
            sys.exit(1)

        raw_float = float(raw_val)
        if not (0.0 <= raw_float <= 1.0):
            print(f"Verifier error: criterion 'hidden_output_matches' raw value must be in [0, 1], got {raw_val}", file=sys.stderr)
            sys.exit(1)

        scores["behaviour"] = raw_float

required = ["build", "no_python", "behaviour"]
for req in required:
    count = seen_names.count(req)
    if count != 1:
        print(f"Verifier error: component '{req}' must appear exactly once, found {count}", file=sys.stderr)
        sys.exit(1)

# Require 0 or 1 for structural scores and [0, 1] for behaviour
build_val = scores["build"]
if build_val not in (0.0, 1.0):
    print(f"Verifier error: build score must be 0 or 1, got {build_val}", file=sys.stderr)
    sys.exit(1)

no_py_val = scores["no_python"]
if no_py_val not in (0.0, 1.0):
    print(f"Verifier error: no_python score must be 0 or 1, got {no_py_val}", file=sys.stderr)
    sys.exit(1)

beh_val = scores["behaviour"]
if not (0.0 <= beh_val <= 1.0):
    print(f"Verifier error: behaviour score must be in [0, 1], got {beh_val}", file=sys.stderr)
    sys.exit(1)

# Preserve raw details for diagnostics
final_details_path.write_text(raw_details_path.read_text(encoding="utf-8"), encoding="utf-8")

# Award behaviour score when build and no_python both equal 1; otherwise award 0
final_reward_val = beh_val if (build_val == 1.0 and no_py_val == 1.0) else 0.0

# Stage the gated reward on the target filesystem
stage_reward_path.write_text(json.dumps({"reward": final_reward_val}, indent=2) + "\n", encoding="utf-8")
EOF

cat "$STAGE_REWARD"
printf '\n'
cat "$FINAL_DETAILS"
printf '\n'
mv "$STAGE_REWARD" "$FINAL_REWARD"

#!/bin/bash
set -euo pipefail

# ─── Harbor test verifier for titlecase-go ───
# Writes reward.json with three scored checks:
#   build      (weight 1): go build ./... passes
#   no_python  (weight 1): no .py files remain AND build passes
#   behaviour  (weight 4): fraction of hidden test lines matched exactly

WORKSPACE="/workspace/repo"
TESTS_DIR="/tests"
LOGS_DIR="/logs/verifier"
mkdir -p "$LOGS_DIR"

# ─── Check 1: build (weight 1) ───
build_score=0
if (cd "$WORKSPACE" && go build ./... >/dev/null 2>&1); then
    build_score=1
fi

# ─── Check 2: no_python (weight 1) ───
# Only awarded if build passes AND no .py files exist
no_python_score=0
py_count=$(find "$WORKSPACE" -name "*.py" 2>/dev/null | wc -l)
if [ "$py_count" -eq 0 ] && [ "$build_score" -eq 1 ]; then
    no_python_score=1
fi

# ─── Check 3: behaviour (weight 4) ───
behaviour_score=0
if [ "$build_score" -eq 1 ]; then
    # Find or build binary
    binary=""
    for candidate in "$WORKSPACE/titlecase-go" "$WORKSPACE/titlecase" "$WORKSPACE/main"; do
        if [ -f "$candidate" ] && [ -x "$candidate" ]; then
            binary="$candidate"
            break
        fi
    done
    
    if [ -z "$binary" ]; then
        (cd "$WORKSPACE" && go build -o titlecase-go . >/dev/null 2>&1) || true
        if [ -f "$WORKSPACE/titlecase-go" ] && [ -x "$WORKSPACE/titlecase-go" ]; then
            binary="$WORKSPACE/titlecase-go"
        fi
    fi
    
    if [ -n "$binary" ] && [ -f "$binary" ] && [ -x "$binary" ]; then
        actual_file="/tmp/actual_hidden_output.txt"
        "$binary" < "$TESTS_DIR/data/hidden_inputs.txt" > "$actual_file" 2>/dev/null || true
        
        total=$(wc -l < "$TESTS_DIR/data/hidden_expected.txt" | tr -d ' ')
        if [ "$total" -gt 0 ] && [ -s "$actual_file" ]; then
            matched=$(paste "$actual_file" "$TESTS_DIR/data/hidden_expected.txt" | awk -F'\t' '$1 == $2 { count++ } END { print count+0 }')
            behaviour_score=$(awk "BEGIN { printf \"%.6f\", $matched / $total }")
        fi
        rm -f "$actual_file"
    fi
fi

# ─── Weighted mean aggregation ───
# Total weight = 1 + 1 + 4 = 6
reward=$(awk "BEGIN { printf \"%.6f\", ($build_score * 1 + $no_python_score * 1 + $behaviour_score * 4) / 6 }")

# ─── Write reward.json ───
cat > "$LOGS_DIR/reward.json" << EOF
{
  "reward": $reward,
  "build": $build_score,
  "no_python": $no_python_score,
  "behaviour": $behaviour_score
}
EOF

# Also write reward.txt
echo "$reward" > "$LOGS_DIR/reward.txt"

echo "VERIFIER FINISHED: reward=$reward, build=$build_score, no_python=$no_python_score, behaviour=$behaviour_score"

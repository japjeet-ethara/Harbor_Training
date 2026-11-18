#!/bin/bash
set -uo pipefail

# Ensure verifier log directory exists
mkdir -p /logs/verifier

# 1. Build check (weight 1)
# `go build ./...` in /workspace/repo passes -> 1, else 0
build_score=0
if (cd /workspace/repo && go build -o /tmp/titlecase_test_bin .); then
    build_score=1
else
    build_score=0
fi

# 2. No Python check (weight 1)
# No .py files anywhere under /workspace/repo AND the build passes -> 1, else 0
no_py_score=0
if [ "$build_score" -eq 1 ]; then
    py_files=$(find /workspace/repo -name "*.py" -type f | wc -l)
    if [ "$py_files" -eq 0 ]; then
        no_py_score=1
    else
        no_py_score=0
    fi
else
    no_py_score=0
fi

# 3. Behaviour check (weight 4)
# Build the Go program, feed it tests/data/hidden_inputs.txt,
# score = share of lines that exactly match tests/data/hidden_expected.txt.
TESTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
hidden_inputs="${TESTS_DIR}/data/hidden_inputs.txt"
hidden_expected="${TESTS_DIR}/data/hidden_expected.txt"

behaviour_score=0.0
if [ "$build_score" -eq 1 ]; then
    tmp_out=$(mktemp)
    (cd /workspace/repo && go run . < "$hidden_inputs" > "$tmp_out" 2>/tmp/go_err.log) || true
    if [ -f "$tmp_out" ] && [ -s "$tmp_out" ]; then
        total_lines=$(wc -l < "$hidden_expected" | tr -d ' ')
        diff_count=$(diff -u "$tmp_out" "$hidden_expected" | grep -c "^+[^+]" || true)
        total_lines=$(echo "$total_lines" | tr -dc '0-9')
        diff_count=$(echo "$diff_count" | tr -dc '0-9')
        if [ -z "$diff_count" ]; then diff_count=0; fi
        matched_count=$((total_lines - diff_count))
        if [ "$matched_count" -lt 0 ]; then
            matched_count=0
        fi
        behaviour_score=$(awk "BEGIN {printf \"%.4f\", $matched_count / $total_lines}")
    fi
    rm -f "$tmp_out"
fi

# Calculate weighted-mean reward:
# weights: build=1, no_python=1, behaviour=4. Sum of weights = 6.
reward=$(awk "BEGIN {printf \"%.4f\", ($build_score * 1 + $no_py_score * 1 + $behaviour_score * 4) / 6.0}")

# Write structured reward.json
cat <<EOF > /logs/verifier/reward.json
{
  "build": $build_score,
  "no_python": $no_py_score,
  "behaviour": $behaviour_score,
  "reward": $reward
}
EOF

echo "Verification complete. Reward: $reward"
cat /logs/verifier/reward.json


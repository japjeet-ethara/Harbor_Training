#!/bin/bash
set -u

TESTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
inputs="${TESTS_DIR}/data/inputs.txt"
expected="${TESTS_DIR}/data/expected.txt"

tmp_out=$(mktemp)
(cd /workspace/repo && go run . < "$inputs" > "$tmp_out" 2>/dev/null)

count=0
line_no=0

exec 3< "$inputs"
exec 4< "$expected"
exec 5< "$tmp_out"

while read -u 3 in_line && read -u 4 exp_line && read -u 5 act_line; do
    line_no=$((line_no + 1))
    if [ "$exp_line" != "$act_line" ]; then
        count=$((count + 1))
        echo "=== Difference #$count (Line $line_no) ==="
        echo "INPUT:    $in_line"
        echo "EXPECTED: $exp_line"
        echo "ACTUAL:   $act_line"
        echo ""
        if [ "$count" -ge 10 ]; then
            break
        fi
    fi
done

rm -f "$tmp_out"


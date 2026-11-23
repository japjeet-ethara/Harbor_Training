#!/usr/bin/env bash
set -euo pipefail

# Build Go executable in current workspace
go build -o /tmp/titlecase_bin .

INPUT_FILE="${1:-tests/data/inputs.txt}"
EXPECTED_FILE="${2:-tests/data/expected.txt}"

if [ ! -f "$INPUT_FILE" ] || [ ! -f "$EXPECTED_FILE" ]; then
    echo "Usage: $0 [inputs.txt] [expected.txt]"
    exit 1
fi

diffs=0
line_no=0

while IFS= read -r inp && IFS= read -r exp <&3; do
    line_no=$((line_no + 1))
    act=$(echo -n "$inp" | /tmp/titlecase_bin)
    if [ "$act" != "$exp" ]; then
        diffs=$((diffs + 1))
        echo "=== Diff #$diffs at line $line_no ==="
        echo "Input   : $inp"
        echo "Expected: $exp"
        echo "Actual  : $act"
        echo ""
        if [ "$diffs" -ge 10 ]; then
            echo "Reached 10 diffs, stopping."
            break
        fi
    fi
done < "$INPUT_FILE" 3< "$EXPECTED_FILE"

rm -f /tmp/titlecase_bin

if [ "$diffs" -eq 0 ]; then
    echo "All checked lines matched byte-for-byte!"
fi

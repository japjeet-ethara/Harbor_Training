#!/bin/sh
# Runs INSIDE the agent image with the task folder mounted at /task:
# freezes the answer sheets, builds the Go port and compares it with the frozen answers.
set -e
cd /task
python3 tests/gen.py
wc -l tests/data/sample/*.txt tests/data/graded/*.txt
cd /task/solution/src
gofmt -l .
go vet .
go build -o /tmp/tc .
echo BUILD_OK
for s in sample graded; do
    /tmp/tc < /task/tests/data/$s/titles.txt > /tmp/$s.out
    if cmp -s /tmp/$s.out /task/tests/data/$s/answers.txt; then
        echo "$s: IDENTICAL"
    else
        echo "$s: DIFFERS"
        diff /tmp/$s.out /task/tests/data/$s/answers.txt | head -30
    fi
done

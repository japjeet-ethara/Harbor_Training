#!/bin/bash
# Negative control for helpers_test.go: in a throwaway copy, delete the İ lower
# entry and the ﬁ upper entry, and expect the tests to fail.
set -u
mkdir /tmp/m && cp /src/*.go /src/go.mod /tools/helpers_test.go /tmp/m/ && cd /tmp/m || exit 2
before=$(grep -cE '^\s0x0130:|^\s0xFB01: +"\\u0046\\u0049"' pycase_tables.go)
sed -i -E '/^\s0x0130:/d; /^\s0xFB01: +"\\u0046\\u0049"/d' pycase_tables.go
after=$(grep -cE '^\s0x0130:|^\s0xFB01: +"\\u0046\\u0049"' pycase_tables.go)
echo "mutated entries: before $before, after $after"
go test -count=1 ./... > /tmp/out.txt 2>&1
echo "go test exit $? (expected non-zero)"
grep -vE '^\s+helpers_test.go:[0-9]+: # ' /tmp/out.txt | head -12

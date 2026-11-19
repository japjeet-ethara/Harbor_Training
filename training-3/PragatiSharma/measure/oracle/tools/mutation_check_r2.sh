#!/bin/bash
# Negative control for TestRegexClasses: in a throwaway copy, delete the dotless-i
# fold entry and the U+001C-U+001F space range, and expect the test to fail.
set -u
mkdir /tmp/m && cp /src/*.go /src/go.mod /tools/helpers_test.go /tmp/m/ && cd /tmp/m || exit 2
before=$(grep -cE '^\s0x0131:|Lo: 0x001C, Hi: 0x001F' pyregex_tables.go)
sed -i -E '/^\s0x0131:/d; /Lo: 0x001C, Hi: 0x001F/d' pyregex_tables.go
after=$(grep -cE '^\s0x0131:|Lo: 0x001C, Hi: 0x001F' pyregex_tables.go)
echo "mutated entries: before $before, after $after"
go test -count=1 -run TestRegexClasses ./... > /tmp/out.txt 2>&1
echo "go test exit $? (expected non-zero)"
grep -vE '^\s+helpers_test.go:[0-9]+: # ' /tmp/out.txt | head -10

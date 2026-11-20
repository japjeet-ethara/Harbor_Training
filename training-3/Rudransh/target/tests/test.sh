#!/bin/bash
export LC_ALL=C
mkdir -p /logs/verifier
build=0; nopy=0; beh=0

cd /workspace/repo 2>/dev/null
if [ "$PWD" = "/workspace/repo" ] && go build ./... > /tmp/build.log 2>&1; then
  build=1
fi

if [ "$build" = 1 ] && [ -z "$(find /workspace/repo -name '*.py' -print -quit)" ]; then
  nopy=1
fi

if [ "$build" = 1 ] && go build -o /tmp/tc_bin . >> /tmp/build.log 2>&1; then
  timeout 300 /tmp/tc_bin < /tests/data/hidden_inputs.txt > /tmp/out.txt 2> /tmp/run.err || true
  total=$(wc -l < /tests/data/hidden_expected.txt)
  beh=$(awk -v total="$total" 'NR==FNR{a[FNR]=$0; next} {if ($0==a[FNR]) c++} END{printf "%.6f", c/total}' \
        /tests/data/hidden_expected.txt /tmp/out.txt)
fi

reward=$(awk -v b="$build" -v n="$nopy" -v h="$beh" 'BEGIN{printf "%.6f", (b*1 + n*1 + h*4)/6}')
printf '{"build": %s, "no_python": %s, "behaviour": %s, "reward": %s}\n' \
  "$build" "$nopy" "$beh" "$reward" > /logs/verifier/reward.json
cat /logs/verifier/reward.json

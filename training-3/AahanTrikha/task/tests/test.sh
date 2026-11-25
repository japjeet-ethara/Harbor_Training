#!/bin/bash
set -uo pipefail
mkdir -p /logs/verifier
LOG=/logs/verifier/env.log
{
  echo "user=$(whoami) pwd=$(pwd)"
  go version 2>&1
  echo "--- repo ---"; ls -la /workspace/repo 2>&1
  echo "--- py files ---"; find /workspace/repo -name '*.py' -print 2>&1 | head -20
} > "$LOG" 2>&1

REPO=/workspace/repo
DATA=/tests/data
BIN=/tmp/titlecase_bin
build=0; nopy=0; beh="0.0000"

# Prerequisite 1: the Go project must build both ways.
if cd "$REPO" 2>/dev/null; then
  go build ./... > "$LOG.build" 2>&1; rc1=$?
  go build -o "$BIN" . >> "$LOG.build" 2>&1; rc2=$?
  if [ "$rc1" -eq 0 ] && [ "$rc2" -eq 0 ]; then build=1; fi
fi

# Prerequisite 2: no Python source may remain in the repo.
if [ "$build" -eq 1 ] && [ -z "$(find "$REPO" -name '*.py' -print -quit)" ]; then
  nopy=1
fi

# Behaviour: compare SHA-256 of each output line with the frozen hash answers.
# Plaintext hidden answers are never shipped, so a binary cannot read the exam.
if [ "$build" -eq 1 ] && [ "$nopy" -eq 1 ]; then
  "$BIN" < "$DATA/hidden_inputs.txt" > /tmp/got.txt 2>/dev/null || true
  tr -d '\r' < "$DATA/answers.sha256.txt" > /tmp/answers.sha
  : > /tmp/got.sha
  while IFS= read -r line || [ -n "$line" ]; do
    line=${line%$'\r'}
    printf '%s' "$line" | sha256sum | cut -d' ' -f1 >> /tmp/got.sha
  done < /tmp/got.txt
  total=$(wc -l < /tmp/answers.sha)
  beh=$(paste /tmp/got.sha /tmp/answers.sha | awk -v t="$total" \
    '$1==$2{n++} END{ if(t>0) printf "%.4f", n/t; else printf "0.0000" }')
fi

# build and no_python are gates only. Reward is behaviour, or 0 if a gate fails.
reward=$(awk -v b="$build" -v n="$nopy" -v p="$beh" \
  'BEGIN{ if(b==1 && n==1) printf "%.4f", p; else printf "0.0000" }')

printf '{"build": %s, "no_python": %s, "behaviour": %s, "reward": %s}\n' \
  "$build" "$nopy" "$beh" "$reward" > /logs/verifier/reward.json
cat /logs/verifier/reward.json

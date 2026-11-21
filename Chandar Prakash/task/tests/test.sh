#!/bin/bash
set -eu

mkdir -p /logs/verifier
chmod 700 /tests/data
chmod 600 /tests/data/inputs.txt /tests/data/answers.txt
if ! python /tests/test_outputs.py; then
  printf '{"reward":0}\n' > /logs/verifier/reward.json
fi

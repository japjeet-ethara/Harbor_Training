#!/bin/bash

mkdir -p /logs/verifier
if ! python /tests/test_outputs.py; then
  printf '{"reward":0}\n' > /logs/verifier/reward.json
fi

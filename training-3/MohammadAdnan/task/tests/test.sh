#!/bin/bash
# Runs the Go grader in tests/checks. Never trusts a reward file that already exists.
mkdir -p /logs/verifier
rm -f /logs/verifier/reward.json /logs/verifier/reward.txt

cd /tests/checks && go run .

if [ ! -s /logs/verifier/reward.json ]; then
  echo '{"reward": 0, "build": 0, "no_python": 0, "behaviour": 0}' > /logs/verifier/reward.json
fi
exit 0

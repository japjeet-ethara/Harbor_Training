#!/bin/bash
set -uo pipefail
mkdir -p /logs/verifier
python3 /tests/grade.py
# grade.py always writes /logs/verifier/reward.json; fail loudly if it did not
test -s /logs/verifier/reward.json

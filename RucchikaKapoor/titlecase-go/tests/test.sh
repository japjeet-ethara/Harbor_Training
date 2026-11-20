#!/bin/bash
set -euo pipefail
mkdir -p /logs/verifier
python3 /tests/grade.py
test -s /logs/verifier/reward.json

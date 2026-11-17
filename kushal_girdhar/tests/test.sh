#!/bin/bash
set -euo pipefail
umask 022
cd /tests
chmod go-w /logs/verifier
python -I /tests/isolate.py
python -m rewardkit /tests --workspace /workspace/repo --output /logs/verifier/reward.json --mcp 1

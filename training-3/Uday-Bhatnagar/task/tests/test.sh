#!/usr/bin/env bash
set -euo pipefail

mkdir -p /logs/verifier
exec python -I /tests/criteria/behaviour.py /workspace/repo /logs/verifier/reward.json

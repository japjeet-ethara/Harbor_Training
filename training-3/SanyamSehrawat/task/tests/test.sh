#!/bin/bash
set -euo pipefail
mkdir -p /logs/verifier
cd /tests
exec go run grade.go /workspace/repo /tests/data/graded /logs/verifier/reward.json

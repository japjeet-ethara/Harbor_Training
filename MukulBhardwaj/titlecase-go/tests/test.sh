#!/bin/bash
set -euo pipefail

exec rewardkit /tests --workspace /workspace/repo --output /logs/verifier/reward.json

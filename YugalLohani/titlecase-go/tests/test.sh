#!/bin/bash
# Harbor verifier for titlecase-go.
#
# Step 1: Generate test data from the original Python titlecase in /workspace/repo.
#         This ensures expected outputs come from the ground-truth Python library,
#         not from any hardcoded file.
#
# Step 2: Run harbor-rewardkit which discovers /tests/grader.py, runs the three
#         weighted criteria, and writes /logs/verifier/reward.json.

set -euo pipefail

mkdir -p /logs/verifier

# ---------------------------------------------------------------------------
# Generate test data if not already present.
# /workspace/repo contains the original python-titlecase source (put there by
# the environment Dockerfile), so we use it as the truth.
# gen.py imports from ../../python-titlecase relative to tests/gen.py, but
# inside the verifier that path doesn't exist — so we override PYTHONPATH.
# ---------------------------------------------------------------------------
if [ ! -f /tests/data/hidden_inputs.txt ]; then
    echo "Generating test data..."
    PYTHONPATH=/workspace/repo python3 /tests/gen_verifier.py
    echo "Test data generated."
fi

# ---------------------------------------------------------------------------
# Run RewardKit — discovers /tests/grader.py and writes reward.json.
# ---------------------------------------------------------------------------
uvx --python '>=3.12,<3.14' \
    --from 'harbor-rewardkit==0.2.*' \
    rewardkit /tests

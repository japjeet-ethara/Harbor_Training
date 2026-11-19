#!/bin/bash
# Verifier entry point. Runs in the separate verifier container after the agent stops.
# Writes /logs/verifier/reward.json: one score per check plus the combined "reward".
#
# Needs network (allowlist: pypi.org, files.pythonhosted.org) to download Reward Kit with uvx.
set -uo pipefail
mkdir -p /logs/verifier

uvx --python '>=3.12,<3.14' --from 'harbor-rewardkit==0.2.*' \
    rewardkit /tests --workspace /workspace/repo --output /logs/verifier/reward.json

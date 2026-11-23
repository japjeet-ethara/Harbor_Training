#!/bin/bash
set -euo pipefail

mkdir -p /logs/verifier
cd /tmp

uvx --python '>=3.12,<3.14' --from 'harbor-rewardkit==0.2.*' rewardkit \
  /tests/checks \
  --workspace /workspace/repo

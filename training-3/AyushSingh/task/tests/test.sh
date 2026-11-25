#!/bin/bash
set -euo pipefail

mkdir -p /logs/verifier
cd /tmp

# Restore the collected /workspace/repo snapshot when running in separate verifier mode
if [ -f /tmp/repo.tar.gz ]; then
  rm -rf /workspace/repo
  mkdir -p /workspace
  tar -C /workspace -xzf /tmp/repo.tar.gz
elif [ -f /logs/artifacts/repo.tar.gz ]; then
  rm -rf /workspace/repo
  mkdir -p /workspace
  tar -C /workspace -xzf /logs/artifacts/repo.tar.gz
fi

cd /workspace/repo

uvx --python '>=3.12,<3.14' --from 'harbor-rewardkit==0.2.*' rewardkit \
  /tests/checks \
  --workspace /workspace/repo

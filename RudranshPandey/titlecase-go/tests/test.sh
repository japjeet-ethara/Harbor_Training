#!/bin/bash
uvx --python '>=3.12,<3.14' --from 'harbor-rewardkit==0.2.4' rewardkit /tests --workspace /workspace/repo --max-concurrent-programmatic 1

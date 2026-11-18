#!/bin/bash
set -euo pipefail

export PATH="/usr/local/go/bin:/usr/local/bin:/usr/bin:/bin"

uvx --python '>=3.12,<3.14' --from 'harbor-rewardkit==0.2.*' rewardkit --workspace /workspace/repo /tests
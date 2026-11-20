#!/bin/bash
set -euo pipefail
if ! command -v uvx >/dev/null 2>&1; then
    apt-get update -qq && apt-get install -y -qq curl >/dev/null
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
fi
uvx --python '>=3.12,<3.14' --from 'harbor-rewardkit==0.2.*' rewardkit /tests
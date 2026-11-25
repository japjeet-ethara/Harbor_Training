#!/bin/bash

apt-get update
apt-get install -y curl ca-certificates

curl -LsSf https://astral.sh/uv/install.sh | sh

source "$HOME/.local/bin/env"

uvx --python '>=3.12,<3.14' --from 'harbor-rewardkit==0.2.*' rewardkit /tests

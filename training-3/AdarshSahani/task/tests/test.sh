#!/bin/bash
set -euo pipefail

mkdir -p /logs/verifier
rm -f /logs/verifier/reward.json

cd /tests
UV_PYTHON_DOWNLOADS=never uv run --no-project --python 3.12 python -m unittest -v test_outputs test_security_processes

# Keep the verifier environment small and prevent Go from using network/cgo.
env -i \
    PATH="/root/.local/bin:/usr/local/go/bin:/usr/bin:/bin" \
    HOME=/root LANG=C.UTF-8 PYTHONUTF8=1 PYTHONIOENCODING=utf-8 \
    GOPROXY=off GOTOOLCHAIN=local CGO_ENABLED=0 \
    GOFLAGS="-mod=readonly -buildvcs=false" \
    rewardkit /tests/checks \
      --workspace /workspace/repo \
      --output /logs/verifier/reward.json \
      --max-concurrent-programmatic 1

if [[ ! -s /logs/verifier/reward.json ]]; then
  echo "rewardkit exited successfully without writing /logs/verifier/reward.json" >&2
  exit 1
fi
python3 -m json.tool /logs/verifier/reward.json >/dev/null

#!/bin/sh
set -eu

# Run only in the dedicated verifier image. Never run Worker as host root.
test -f /tests/.container-verifier || {
    echo 'Infrastructure error: use the dedicated Docker verifier image.' >&2
    exit 2
}
test "$(id -u)" = 0 || {
    echo 'Infrastructure error: RewardKit Worker requires verifier root.' >&2
    exit 2
}
mkdir -p /logs/verifier /run/titlecase-grader
chmod 700 /tests /logs/verifier /run/titlecase-grader
rm -f /logs/verifier/reward.json /logs/verifier/reward.txt
export PYTHONPATH=/tests
export LITELLM_LOCAL_MODEL_COST_MAP=True
exec python -m rewardkit /tests \
    --workspace /workspace/repo \
    --output /logs/verifier/reward.json \
    --max-concurrent-programmatic 1

#!/usr/bin/env bash
set -euo pipefail

root=$(cd -- "$(dirname -- "$0")/.." && pwd)
output=$(mktemp -d "${TMPDIR:-/tmp}/titlecase-harbor.XXXXXXXX")
mkdir -p "$output/jobs"
export PYTHONDONTWRITEBYTECODE=1
cd -- "$output"
{
    set -x
    harbor --version
    docker version
    docker compose version
    harbor lint --select ALL "$root"
    docker build --tag titlecase-go-agent:section18 "$root/environment"
    docker run --rm --network none titlecase-go-agent:section18 bash -ec \
        'test "$PWD" = /workspace/repo; test -f titlecase/__init__.py; test ! -e /tests; go version; python -c "import regex, titlecase; assert titlecase.REGEX_AVAILABLE; print(regex.__version__)"'
    docker build --tag titlecase-go-verifier:section18 "$root/tests"
    docker run --rm --network none -e LITELLM_LOCAL_MODEL_COST_MAP=True titlecase-go-verifier:section18 \
        bash -ec 'test -s /tests/data/hidden_expected.txt; rewardkit --help >/dev/null'
    python "$root/tools/replay_task.py" "$output/replay-task"
    harbor run -p "$root" --env docker -a oracle --jobs-dir "$output/jobs" --job-name oracle
    harbor run -p "$root" --env docker -a nop --jobs-dir "$output/jobs" --job-name nop
    harbor run -p "$output/replay-task" --env docker -a oracle --jobs-dir "$output/jobs" --job-name replay
    python "$root/tools/verify_harbor_rewards.py" "$output/jobs"
} 2>&1 | tee "$output/harbor.log"
printf 'Harbor jobs and logs in %s\n' "$output"

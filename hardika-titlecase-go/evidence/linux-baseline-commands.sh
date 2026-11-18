#!/usr/bin/env bash
set -euo pipefail
source /root/harbor-vm-tools/env/bin/activate
export TMPDIR=/root/section18-runs PYTHONDONTWRITEBYTECODE=1
cd /root/section18
output=$(mktemp -d "$TMPDIR/titlecase-harbor.XXXXXXXX")
mkdir -p "$output/jobs"
set -x
python tools/replay_task.py "$output/replay-task"
harbor run -p /root/section18 --env docker -a oracle --jobs-dir "$output/jobs" --job-name oracle
harbor run -p /root/section18 --env docker -a nop --jobs-dir "$output/jobs" --job-name nop
harbor run -p "$output/replay-task" --env docker -a oracle --jobs-dir "$output/jobs" --job-name replay
python tools/verify_harbor_rewards.py "$output/jobs"
printf 'Harbor jobs in %s\n' "$output"

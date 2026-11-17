#!/bin/bash
set -euo pipefail
task="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
out="$(mktemp -d "${1:-$PWD}/titlecase-validation.XXXXXXXX")"
exec > >(tee -a "$out/validation.log") 2>&1
export HF_HUB_OFFLINE=1
export LITELLM_LOCAL_MODEL_COST_MAP=True LITELLM_TELEMETRY=False DO_NOT_TRACK=1
printf 'Evidence directory %s\n' "$out"
run() {
    local status=0
    printf '+'
    printf ' %q' "$@"
    printf '\n'
    "$@" || status=$?
    printf 'Exit status %d\n' "$status"
    return "$status"
}
run date -u +%FT%TZ
run harbor --version
run docker version
run docker compose version
cp -- "$task/task.toml" "$out/task.toml"
run harbor lint "$task" --select ALL --json
run docker build -t titlecase-s18-agent-check "$task/environment"
run docker build -t titlecase-s18-verifier-check "$task/tests"
run docker run --rm --network none --user candidate titlecase-s18-agent-check sh -ec '
    test "$PWD" = /workspace/repo
    test -r titlecase/__init__.py
    test -w /workspace/repo
    test ! -e /tests
    test ! -e /solution
    go version
'
run docker run --rm --network none --user 65534 titlecase-s18-verifier-check sh -ec '
    test ! -r /tests/data/hidden_inputs.txt
    test ! -r /tests/data/hidden_expected.txt
'
replay="$out/replay-task"
mkdir -p "$replay/solution"
cp -a -- "$task/environment" "$task/tests" "$task/task.toml" "$task/instruction.md" "$replay/"
cp -- "$task/cheat/solve.sh" "$replay/solution/solve.sh"
cp -- "$task/tests/data/expected.txt" "$replay/solution/visible-answers.txt"
run harbor run -p "$task" -a oracle --jobs-dir "$out/jobs" --job-name oracle
run harbor run -p "$task" -a nop --jobs-dir "$out/jobs" --job-name nop
run harbor run -p "$replay" -a oracle --jobs-dir "$out/jobs" --job-name replay
run python3 "$task/tools/check_harbor_rewards.py" "$out/jobs"

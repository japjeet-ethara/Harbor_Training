#!/bin/bash
set -euo pipefail
export PATH="$HOME/.local/bin:$PATH"
root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
stamp=$(date -u +%Y%m%dT%H%M%SZ)
run="$root/evidence/harbor/$stamp"
mkdir -p "$run"
exec > >(tee "$run/commands.log") 2>&1
set -x
harbor --version
docker version
docker compose version
harbor lint "$root/titlecase-go" --select ALL --json > "$run/lint.json"
harbor run -p "$root/titlecase-go" -a oracle -o "$run/jobs" --job-name oracle --n-concurrent 1
harbor run -p "$root/titlecase-go" -a nop -o "$run/jobs" --job-name nop --n-concurrent 1
temp=$(mktemp -d)
trap 'rm -rf "$temp"' EXIT
cp -a "$root/titlecase-go" "$temp/replay-task"
cp "$root/titlecase-go/cheat/solve.sh" "$temp/replay-task/solution/solve.sh"
cp "$root/titlecase-go/cheat/visible-output.txt" "$temp/replay-task/solution/visible-output.txt"
sha256sum "$root/titlecase-go/solution/solve.sh" > "$run/real-solution-before.sha256"
harbor run -p "$temp/replay-task" -a oracle -o "$run/jobs" --job-name replay-cheat --n-concurrent 1
sha256sum "$root/titlecase-go/solution/solve.sh" > "$run/real-solution-after.sha256"
cmp "$run/real-solution-before.sha256" "$run/real-solution-after.sha256"
python3 "$root/tools/summarize_harbor.py" "$run"

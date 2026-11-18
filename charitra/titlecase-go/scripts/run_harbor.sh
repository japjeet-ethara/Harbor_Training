#!/usr/bin/env bash
# Execute real Docker trials. Never substitute local mocks for Harbor evidence.
set -euo pipefail

task_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
run_root="$task_root/evidence/harbor/$(date -u +%Y%m%dT%H%M%SZ)"
if [[ $# -gt 0 ]]; then
    if [[ $# != 2 || "$1" != --output ]]; then
        echo "Usage: bash scripts/run_harbor.sh [--output DIRECTORY]" >&2
        exit 2
    fi
    run_root="$2"
fi
for program in harbor docker python3; do
    command -v "$program" >/dev/null || {
        echo "Missing $program. Follow README setup before running this script." >&2
        exit 2
    }
done
[[ "$(harbor --version)" == 0.25.0 ]] || {
    echo 'This task is verified against harbor==0.25.0; install that version.' >&2
    exit 2
}
docker compose version >/dev/null
docker info >/dev/null
mkdir -p "$run_root"
run_root="$(cd -- "$run_root" && pwd)"
if [[ -e "$run_root/run-manifest.json" || -e "$run_root/jobs" ]]; then
    echo "Output already contains a run. Choose a new --output directory: $run_root" >&2
    exit 2
fi
mkdir -p "$run_root/jobs" "$run_root/task-copies"
{
    date -u +%Y-%m-%dT%H:%M:%SZ
    harbor --version
    docker version
    docker compose version
    python3 --version
} > "$run_root/preflight.txt"

# Copy a dedicated negative-control task. The canonical task/solution remains intact.
python3 - "$task_root" "$run_root" <<'PY'
from pathlib import Path
import hashlib, json, shutil, sys
from datetime import datetime, timezone
source, output = map(Path, sys.argv[1:])
cheat = output / 'task-copies/titlecase-go-replay'
shutil.copytree(source, cheat, ignore=shutil.ignore_patterns('evidence', '__pycache__', '*.pyc', '.git'))
shutil.rmtree(cheat / 'solution')
(cheat / 'solution').mkdir()
shutil.copyfile(source / 'cheat/solve.sh', cheat / 'solution/solve.sh')
(cheat / 'solution/solve.sh').chmod(0o755)
tracked = ['task.toml', 'environment/Dockerfile', 'tests/Dockerfile', 'tests/grader.py',
           'tests/reward.toml', 'tests/data/manifest.json', 'solution/solve.sh',
           'solution/main.go', 'solution/unicode_tables.go', 'cheat/solve.sh']
manifest = {
    'schema_version': 1,
    'status': 'started',
    'started_at': datetime.now(timezone.utc).isoformat(),
    'task_root': str(source),
    'versions': {'harbor': '0.25.0', 'harbor-rewardkit': '0.2.4', 'go': '1.23'},
    'environment': {'type': 'docker', 'auto_mounting': False, 'network_mode': 'no-network',
                    'verifier_environment_mode': 'separate'},
    'task_file_sha256': {p: hashlib.sha256((source / p).read_bytes()).hexdigest() for p in tracked},
    'jobs': {'oracle': 'jobs/oracle', 'nop': 'jobs/nop', 'cheat': 'jobs/cheat'},
    'cheat': 'Replay visible answers while retaining Python files; required reward < 0.2.',
}
(output / 'run-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
PY

run_one() {
    local label="$1" agent="$2" task_path="$3"
    printf 'Running %s in Docker; output: %s\n' "$label" "$run_root/jobs/$label"
    harbor run \
        -p "$task_path" \
        -a "$agent" \
        -e docker \
        -n 1 -k 1 \
        -o "$run_root/jobs" \
        --job-name "$label" \
        --ek auto_mounting=false
}
run_one oracle oracle "$task_root"
run_one nop nop "$task_root"
run_one cheat oracle "$run_root/task-copies/titlecase-go-replay"
python3 "$task_root/scripts/verify_evidence.py" "$run_root"
printf '\nValidated Harbor evidence: %s\n' "$run_root/evidence-summary.json"
printf 'View runs: harbor view "%s/jobs" --port 8080\n' "$run_root"

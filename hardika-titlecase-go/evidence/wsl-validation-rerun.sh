#!/usr/bin/env bash
set -uo pipefail

shared=$PWD
scratch=/tmp/titlecase-wsl.yqs3RQvx
install -m 0755 "$shared/hardika-titlecase-go/tools/run_harbor.sh" "$scratch/task/tools/run_harbor.sh"
source "$scratch/venv/bin/activate"
export PYTHONDONTWRITEBYTECODE=1 TMPDIR="$scratch/runs"
cd "$scratch/task"
set -x
bash tools/run_harbor.sh
status=$?
python - "$scratch" "$shared/wsl-results-final.tar.gz" <<'PY'
from pathlib import Path
import sys
import tarfile

root = Path(sys.argv[1])
keep = {"config.json", "result.json", "job.log", "trial.log", "lock.json",
        "reward.json", "reward-details.json", "test-stdout.txt", "test-stderr.txt",
        "oracle.txt", "exit-code.txt", "exception.txt", "harbor.log"}
with tarfile.open(sys.argv[2], "w:gz") as output:
    output.add(root / "host-versions.txt", arcname="host-versions.txt")
    for path in sorted((root / "runs").rglob("*")):
        if path.is_file() and path.name in keep and "artifacts" not in path.parts:
            output.add(path, arcname=path.relative_to(root / "runs").as_posix())
PY
exit "$status"

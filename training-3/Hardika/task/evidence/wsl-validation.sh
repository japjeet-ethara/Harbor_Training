#!/usr/bin/env bash
set -uo pipefail

publish_dir=$PWD
scratch=$(mktemp -d /tmp/titlecase-wsl.XXXXXXXX)
mkdir -p "$scratch/task" "$scratch/runs"
tar -xzf "$publish_dir/wsl-task.tgz" -C "$scratch/task" || exit
export UV_CACHE_DIR="$scratch/uv-cache" UV_PYTHON_INSTALL_DIR="$scratch/uv-python"
export PYTHONDONTWRITEBYTECODE=1 TMPDIR="$scratch/runs"
set -x
uname -a
docker version
docker compose version
python3 -VV
uv --version
uv venv --python "$(command -v python3)" "$scratch/venv" || exit
uv pip install --python "$scratch/venv/bin/python" harbor==0.26.0 || exit
uv pip freeze --python "$scratch/venv/bin/python" > "$scratch/host-versions.txt"
source "$scratch/venv/bin/activate"
bash "$scratch/task/tools/run_harbor.sh"
status=$?
python - "$scratch" "$publish_dir/wsl-results.tar.gz" <<'PY'
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

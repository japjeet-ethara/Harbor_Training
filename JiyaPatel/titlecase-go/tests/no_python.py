import subprocess
from pathlib import Path
import rewardkit as rk

repo = Path("/workspace/repo")
no_py = len(list(repo.rglob("*.py"))) == 0
build_ok = subprocess.run(["go", "build", "./..."], cwd=repo, capture_output=True).returncode == 0
rk.record(no_py and build_ok)

import os
from pathlib import Path
import subprocess
import rewardkit as rk

@rk.criterion(description="go build ./... succeeds in /workspace/repo")
def check_build(workspace: Path) -> float:
    repo = "/workspace/repo" if os.path.exists("/workspace/repo") else str(workspace)
    env = os.environ.copy()
    env["PATH"] = "/usr/local/go/bin:/go/bin:" + env.get("PATH", "")
    res = subprocess.run(
        ["go", "build", "-o", "/tmp/titlecase_build_check", "./..."],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
    )
    return 1.0 if res.returncode == 0 else 0.0
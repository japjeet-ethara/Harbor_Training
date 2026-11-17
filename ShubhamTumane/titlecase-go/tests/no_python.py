import os
from pathlib import Path
import subprocess
import rewardkit as rk

@rk.criterion(description="no .py files in /workspace/repo and go build succeeds")
def check_no_python(workspace: Path) -> float:
    repo = "/workspace/repo" if os.path.exists("/workspace/repo") else str(workspace)
    py_files = []
    for root, _, files in os.walk(repo):
        for f in files:
            if f.endswith(".py"):
                py_files.append(os.path.join(root, f))

    env = os.environ.copy()
    env["PATH"] = "/usr/local/go/bin:/go/bin:" + env.get("PATH", "")
    res = subprocess.run(
        ["go", "build", "-o", "/tmp/titlecase_nopy_check", "./..."],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
    )
    return 1.0 if (len(py_files) == 0 and res.returncode == 0) else 0.0
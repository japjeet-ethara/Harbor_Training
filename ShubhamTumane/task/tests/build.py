import importlib.util
import os
from pathlib import Path
import subprocess
import rewardkit as rk

def _eval_behaviour(workspace: Path) -> float:
    beh_path = Path(__file__).resolve().parent / "behaviour.py"
    spec = importlib.util.spec_from_file_location("_beh_helper", beh_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.evaluate_behaviour(workspace)

@rk.criterion(description="go build ./... succeeds and passes minimum behaviour gate")
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
        timeout=180,
    )
    if res.returncode != 0:
        return 0.0
    return 1.0 if _eval_behaviour(workspace) > 0.25 else 0.0
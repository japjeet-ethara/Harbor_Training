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

@rk.criterion(description="no .py files, Python artifacts, or runtime interpreter invocations")
def check_no_python(workspace: Path) -> float:
    repo = "/workspace/repo" if os.path.exists("/workspace/repo") else str(workspace)
    for check_dir in [repo, "/tmp", "/var/tmp"]:
        if not os.path.exists(check_dir):
            continue
        for root, _, files in os.walk(check_dir):
            for f in files:
                if check_dir == repo and f.endswith((".py", ".pyc", ".sh")):
                    return 0.0
                if check_dir != repo and "titlecase" in f.lower() and f.endswith((".py", ".pyc")):
                    return 0.0
                if check_dir == repo:
                    full_path = os.path.join(root, f)
                    content = Path(full_path).read_text(encoding="utf-8", errors="ignore").lower()
                    if f.endswith(".go") and ("os/exec" in content or "python" in content or "syscall" in content):
                        return 0.0

    env = os.environ.copy()
    env["PATH"] = "/usr/local/go/bin:/go/bin:" + env.get("PATH", "")
    bin_path = "/tmp/titlecase_nopy_check"
    res = subprocess.run(
        ["go", "build", "-o", bin_path, "./..."],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
        timeout=180,
    )
    if res.returncode != 0 or not os.path.exists(bin_path):
        return 0.0

    bin_bytes = Path(bin_path).read_bytes().lower()
    if b"python3" in bin_bytes or b"python" in bin_bytes or b"/bin/sh" in bin_bytes or b"/bin/bash" in bin_bytes:
        return 0.0

    os.chmod(bin_path, 0o755)
    probe = subprocess.run(
        ["su", "-s", "/bin/sh", "nobody", "-c", f"env -i PATH=/nonexistent {bin_path}"],
        input=b"the quick brown fox\n",
        capture_output=True,
        timeout=30,
    )
    if probe.returncode != 0 or probe.stdout.strip() != b"The Quick Brown Fox":
        return 0.0

    return 1.0 if _eval_behaviour(workspace) > 0.25 else 0.0
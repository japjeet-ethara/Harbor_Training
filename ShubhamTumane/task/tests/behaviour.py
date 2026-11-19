import os
from pathlib import Path
import subprocess
import rewardkit as rk

@rk.criterion(description="line-by-line exact match against hidden dataset")
def check_behaviour(workspace: Path) -> float:
    repo = "/workspace/repo" if os.path.exists("/workspace/repo") else str(workspace)
    env = os.environ.copy()
    env["PATH"] = "/usr/local/go/bin:/go/bin:" + env.get("PATH", "")
    bin_path = "/tmp/titlecase_bin"
    build_res = subprocess.run(
        ["go", "build", "-o", bin_path, "."],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
    )
    if build_res.returncode != 0 or not os.path.exists(bin_path):
        return 0.0

    tests_dir = Path(__file__).resolve().parent
    hidden_in = tests_dir / "data" / "hidden_inputs.txt"
    hidden_exp = tests_dir / "data" / "hidden_expected.txt"

    with open(hidden_in, "r", encoding="utf-8") as f_in:
        run_res = subprocess.run(
            [bin_path],
            stdin=f_in,
            capture_output=True,
            text=True,
        )
    if run_res.returncode != 0:
        return 0.0

    actual_lines = [line.rstrip("\r\n") for line in run_res.stdout.splitlines()]
    with open(hidden_exp, "r", encoding="utf-8") as f_exp:
        exp_lines = [line.rstrip("\r\n") for line in f_exp.readlines()]

    if not exp_lines:
        return 0.0

    matches = sum(1 for a, b in zip(actual_lines, exp_lines) if a == b)
    return matches / len(exp_lines)
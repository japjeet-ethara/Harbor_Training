import os
from pathlib import Path
import subprocess
import rewardkit as rk

def passes_no_python_static_and_runtime(repo: str, bin_path: str) -> bool:
    for check_dir in [repo, "/tmp", "/var/tmp"]:
        if not os.path.exists(check_dir):
            continue
        for root, _, files in os.walk(check_dir):
            for f in files:
                if check_dir == repo and f.endswith((".py", ".pyc", ".sh")):
                    return False
                if check_dir != repo and "titlecase" in f.lower() and f.endswith((".py", ".pyc")):
                    return False
                if check_dir == repo and f.endswith(".go"):
                    full_path = os.path.join(root, f)
                    content = Path(full_path).read_text(encoding="utf-8", errors="ignore").lower()
                    if "os/exec" in content or "python" in content or "syscall" in content:
                        return False

    if not os.path.exists(bin_path):
        return False

    bin_bytes = Path(bin_path).read_bytes().lower()
    if b"python3" in bin_bytes or b"python" in bin_bytes or b"/bin/sh" in bin_bytes or b"/bin/bash" in bin_bytes:
        return False

    os.chmod(bin_path, 0o755)
    probe = subprocess.run(
        ["su", "-s", "/bin/sh", "nobody", "-c", f"env -i PATH=/nonexistent {bin_path}"],
        input=b"the quick brown fox\n",
        capture_output=True,
        timeout=30,
    )
    return probe.returncode == 0 and probe.stdout.strip() == b"The Quick Brown Fox"

def evaluate_behaviour(workspace: Path) -> float:
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
        timeout=180,
    )
    if build_res.returncode != 0 or not os.path.exists(bin_path):
        return 0.0

    if not passes_no_python_static_and_runtime(repo, bin_path):
        return 0.0

    tests_dir = Path(__file__).resolve().parent
    data_dir = tests_dir / "data"
    hidden_in = data_dir / "inputs.txt"
    hidden_exp = data_dir / "answers.txt"

    in_bytes = hidden_in.read_bytes()
    in_lines = in_bytes.decode("utf-8").split("\n")[:-1]
    exp_lines = hidden_exp.read_text(encoding="utf-8").split("\n")[:-1]
    if not exp_lines:
        return 0.0

    os.chmod(data_dir, 0o000)
    try:
        run_res = subprocess.run(
            ["su", "-s", "/bin/sh", "nobody", "-c", bin_path],
            input=in_bytes,
            capture_output=True,
            timeout=180,
        )
    finally:
        os.chmod(data_dir, 0o755)

    if run_res.returncode != 0:
        return 0.0

    stdout_text = run_res.stdout.decode("utf-8", errors="replace")
    if stdout_text.endswith("\n"):
        stdout_text = stdout_text[:-1]
    actual_lines = stdout_text.split("\n") if stdout_text != "" else []

    if len(actual_lines) != len(exp_lines):
        return 0.0

    transformed_indices = [i for i, (x, y) in enumerate(zip(in_lines, exp_lines)) if x != y]
    if not transformed_indices:
        return 0.0

    unchanged_ok = all(actual_lines[i] == exp_lines[i] for i, (x, y) in enumerate(zip(in_lines, exp_lines)) if x == y)
    if not unchanged_ok:
        return 0.0

    matches = sum(1 for i in transformed_indices if actual_lines[i] == exp_lines[i])
    return matches / len(transformed_indices)

@rk.criterion(description="line-by-line exact match against 100k dataset (pure Go only)")
def check_behaviour(workspace: Path) -> float:
    return evaluate_behaviour(workspace)
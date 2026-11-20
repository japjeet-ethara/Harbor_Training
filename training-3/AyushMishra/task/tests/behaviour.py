from pathlib import Path
import subprocess
import tempfile
import os
from rewardkit import criterion

REPO_DIR = Path("/workspace/repo")
TESTS_DIR = Path(__file__).resolve().parent
HIDDEN_INPUTS_PATH = TESTS_DIR / "data" / "hidden_inputs.txt"
HIDDEN_EXPECTED_PATH = TESTS_DIR / "data" / "hidden_expected.txt"


@criterion
def check_behaviour(workspace: Path) -> float:
    repo_path = REPO_DIR if REPO_DIR.exists() else workspace

    if not HIDDEN_INPUTS_PATH.exists() or not HIDDEN_EXPECTED_PATH.exists():
        return 0.0

    with open(HIDDEN_EXPECTED_PATH, "r", encoding="utf-8") as f:
        expected_lines = [line.rstrip("\r\n") for line in f]

    total_lines = len(expected_lines)
    if total_lines == 0:
        return 0.0

    # Build the Go program into a temporary binary
    with tempfile.TemporaryDirectory() as tmpdir:
        bin_path = os.path.join(tmpdir, "titlecase_app")
        try:
            build_res = subprocess.run(
                ["go", "build", "-o", bin_path, "."],
                cwd=str(repo_path),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=120,
            )
            if build_res.returncode != 0:
                # If building '.' fails, try building main package if in cmd/ or ./...
                build_res = subprocess.run(
                    ["go", "build", "-o", bin_path, "./..."],
                    cwd=str(repo_path),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=120,
                )
                if build_res.returncode != 0:
                    return 0.0
        except Exception:
            return 0.0

        # Feed tests/data/hidden_inputs.txt to the Go binary via stdin
        try:
            with open(HIDDEN_INPUTS_PATH, "r", encoding="utf-8") as infile:
                run_res = subprocess.run(
                    [bin_path],
                    stdin=infile,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    encoding="utf-8",
                    timeout=120,
                )
            if run_res.returncode != 0:
                return 0.0

            actual_lines = [line.rstrip("\r\n") for line in run_res.stdout.splitlines()]
        except Exception:
            return 0.0

    # Score = share of lines that exactly match tests/data/hidden_expected.txt
    matches = 0
    for i in range(min(len(actual_lines), total_lines)):
        if actual_lines[i] == expected_lines[i]:
            matches += 1

    return float(matches) / float(total_lines)

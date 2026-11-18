
"""Behaviour criterion: compare Go output with hidden expected answers."""

from pathlib import Path
import subprocess

from rewardkit import criterion


@criterion
def behaviour(workspace: Path) -> float:
    repo_dir = Path("/workspace/repo")

    if not repo_dir.exists():
        repo_dir = workspace

    if not repo_dir.exists():
        return 0.0

    tests_dir = Path("/tests/data")

    if not tests_dir.exists():
        tests_dir = Path(__file__).parent / "data"

    input_file = tests_dir / "hidden_inputs.txt"
    expected_file = tests_dir / "hidden_expected.txt"

    if not input_file.exists() or not expected_file.exists():
        return 0.0

    try:
        build_result = subprocess.run(
            ["go", "build", "-o", "/tmp/titlecase", "./..."],
            cwd=str(repo_dir),
            capture_output=True,
            text=True,
            timeout=120,
        )

        if build_result.returncode != 0:
            return 0.0

        input_text = input_file.read_text(encoding="utf-8")
        input_lines = input_text.splitlines()

        expected_lines = expected_file.read_text(
            encoding="utf-8"
        ).splitlines()

        run_result = subprocess.run(
            ["/tmp/titlecase"],
            input=input_text,
            capture_output=True,
            text=True,
            timeout=120,
        )

        if run_result.returncode != 0:
            return 0.0

        actual_lines = run_result.stdout.splitlines()

        actual_lines = run_result.stdout.splitlines()

        if not expected_lines:
            return 0.0

        matches = sum(
            1
            for expected, actual in zip(expected_lines, actual_lines)
            if expected == actual
        )

        score = matches / max(len(expected_lines), len(actual_lines))

        return score

    except (OSError, subprocess.TimeoutExpired):
        return 0.0


"""Compare the complete Go output with protected reference answers."""

import os
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

    input_file = tests_dir / "inputs.txt"
    expected_file = tests_dir / "answers.txt"
    legacy_input_file = tests_dir / "legacy-2k" / "inputs.txt"
    legacy_expected_file = tests_dir / "legacy-2k" / "answers.txt"

    if not all(path.is_file() for path in (
        input_file, expected_file, legacy_input_file, legacy_expected_file
    )):
        return 0.0

    # The verifier owns the answer file. Run the candidate as an unprivileged
    # user so it cannot read verifier-only files mounted in this container.
    if os.geteuid() != 0:
        return 0.0

    try:
        expected_file.chmod(0o400)
        legacy_expected_file.chmod(0o400)
        build_result = subprocess.run(
            ["go", "build", "-o", "/tmp/titlecase", "./..."],
            cwd=str(repo_dir),
            capture_output=True,
            text=True,
            timeout=120,
        )

        if build_result.returncode != 0:
            return 0.0

        input_text = (
            input_file.read_text(encoding="utf-8")
            + legacy_input_file.read_text(encoding="utf-8")
        )
        expected_lines = (
            expected_file.read_text(encoding="utf-8").splitlines()
            + legacy_expected_file.read_text(encoding="utf-8").splitlines()
        )

        def drop_candidate_privileges() -> None:
            os.setgroups([])
            os.setgid(65534)
            os.setuid(65534)

        candidate_env = {
            "PATH": "/usr/local/go/bin:/usr/bin:/bin",
            "HOME": "/tmp",
            "LANG": "C.UTF-8",
        }

        run_result = subprocess.run(
            ["/tmp/titlecase"],
            input=input_text,
            capture_output=True,
            text=True,
            timeout=120,
            env=candidate_env,
            preexec_fn=drop_candidate_privileges,
        )

        if run_result.returncode != 0:
            return 0.0

        actual_lines = run_result.stdout.splitlines()

        if not expected_lines or len(input_text.splitlines()) != len(expected_lines):
            return 0.0

        return 1.0 if actual_lines == expected_lines else 0.0

    except (OSError, subprocess.TimeoutExpired):
        return 0.0

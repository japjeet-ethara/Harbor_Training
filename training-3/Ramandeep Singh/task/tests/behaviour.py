
"""
Criterion 3: behaviour (weight 4)

Run the candidate Go program as an unprivileged user.
Protect hidden test data from candidate access.
Score the fraction of matching output lines.
"""

import os
import pwd
import subprocess
import tempfile
from pathlib import Path

try:
    from rewardkit import criterion
except ImportError:
    def criterion(fn):
        return fn


@criterion
def check_behaviour(workspace: Path) -> float:
    try:
        if os.name != "posix" or os.geteuid() != 0:
            return 0.0

        nobody = pwd.getpwnam("nobody")

        data_dir = Path(__file__).resolve().parent / "data"
        inputs_path = data_dir / "hidden_inputs.txt"
        expected_path = data_dir / "hidden_expected.txt"

        if not inputs_path.is_file():
            inputs_path = data_dir / "inputs.txt"
        if not expected_path.is_file():
            expected_path = data_dir / "answers.txt"

        if not inputs_path.is_file() or not expected_path.is_file():
            return 0.0

        # Read verifier data before restricting candidate access.
        input_bytes = inputs_path.read_bytes()
        expected_lines = expected_path.read_text(
            encoding="utf-8"
        ).splitlines()

        if not expected_lines:
            return 0.0
        
        # Reject direct use of Go's process-execution package.
        import_res = subprocess.run(
            ["go", "list", "-f", "{{join .Imports \"\\n\"}}", "."],
            cwd=str(workspace),
            capture_output=True,
            text=True,
            timeout=60,
        )

        if import_res.returncode != 0:
            return 0.0

        direct_imports = set(import_res.stdout.splitlines())

        if "os/exec" in direct_imports:
            return 0.0

        # Protect hidden files and their containing directory.
        expected_path.chmod(0o600)
        data_dir.chmod(0o700)

        with tempfile.TemporaryDirectory() as build_dir:
            build_path = Path(build_dir)
            build_path.chmod(0o755)

            bin_path = build_path / "titlecase_eval"

            build_res = subprocess.run(
                ["go", "build", "-o", str(bin_path), "."],
                cwd=str(workspace),
                capture_output=True,
                timeout=120,
            )

            if build_res.returncode != 0:
                return 0.0

            bin_path.chmod(0o755)

            with tempfile.TemporaryDirectory() as run_dir:
                run_path = Path(run_dir)
                run_path.chmod(0o755)

                run_res = subprocess.run(
                    [str(bin_path)],
                    cwd=str(run_path),
                    input=input_bytes,
                    capture_output=True,
                    timeout=120,
                    env={
                        "PATH": "/usr/bin:/bin",
                        "HOME": str(run_path),
                        "TMPDIR": str(run_path),
                    },
                    user=nobody.pw_uid,
                    group=nobody.pw_gid,
                )

            if run_res.returncode != 0:
                return 0.0

            actual_lines = run_res.stdout.decode(
                "utf-8", errors="replace"
            ).splitlines()

            matches = sum(
                1 for i, expected in enumerate(expected_lines)
                if i < len(actual_lines)
                and actual_lines[i] == expected
            )

            return matches / len(expected_lines)

    except Exception:
        return 0.0


if __name__ == "__main__":
    import sys
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace/repo")
    print(check_behaviour(target))

import os
from pathlib import Path
import pwd
import subprocess
from rewardkit import criterion

DATA_DIR = Path("/tests/data")
BIN_PATH = Path("/tmp/titlecase_verifier_bin")


@criterion(description="fraction of hidden 100k inputs matching Python titlecase() byte-for-byte")
def hidden_behaviour_match(workspace: Path) -> float:
    build = subprocess.run(
        ["go", "build", "-o", str(BIN_PATH), "."],
        cwd=workspace,
        capture_output=True,
        text=True,
        timeout=120,
    )
    if build.returncode != 0 or not BIN_PATH.is_file():
        return 0.0

    # Ensure binary is executable by runner
    os.chmod(BIN_PATH, 0o755)

    inputs_file = DATA_DIR / "inputs.txt"
    answers_file = DATA_DIR / "answers.txt"

    if not inputs_file.is_file() or not answers_file.is_file():
        return 0.0

    inputs_bytes = inputs_file.read_bytes()
    expected_bytes = answers_file.read_bytes()
    expected_lines = expected_bytes.splitlines()
    if not expected_lines:
        return 0.0

    # Temporarily remove answers from disk so cheating binary cannot read them
    answers_file.unlink()

    actual_lines = []
    try:
        # Run binary as unprivileged runner in /tmp
        pw = pwd.getpwnam("runner")
        clean_env = {
            "PATH": "/usr/local/go/bin:/bin:/usr/bin",
            "HOME": pw.pw_dir,
            "CGO_ENABLED": "0",
        }
        run = subprocess.run(
            [str(BIN_PATH)],
            cwd="/tmp",
            user=pw.pw_uid,
            group=pw.pw_gid,
            input=inputs_bytes,
            capture_output=True,
            timeout=300,
            env=clean_env,
        )
        if run.returncode != 0:
            return 0.0
        actual_lines = run.stdout.splitlines()
    except Exception:
        return 0.0
    finally:
        # Restore answers file
        answers_file.write_bytes(expected_bytes)
        BIN_PATH.unlink(missing_ok=True)

    matches = sum(
        1 for exp, act in zip(expected_lines, actual_lines) if exp == act
    )
    denom = max(len(expected_lines), len(actual_lines))
    if denom == 0:
        return 0.0
    return matches / denom

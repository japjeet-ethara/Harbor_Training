import os
from pathlib import Path
import shutil
import subprocess
import tempfile

from rewardkit import criterion

REPO_DIR = Path("/workspace/repo")
TESTS_DIR = Path(__file__).resolve().parent
HIDDEN_INPUTS_PATH = TESTS_DIR / "data" / "inputs_100k.txt"
HIDDEN_EXPECTED_PATH = TESTS_DIR / "data" / "answers_100k.txt"


@criterion
def check_behaviour(workspace: Path) -> float:
    return score_behaviour(workspace)


def score_behaviour(workspace: Path) -> float:
    repo_path = REPO_DIR if REPO_DIR.exists() else workspace

    try:
        hidden_inputs = HIDDEN_INPUTS_PATH.read_bytes()
        expected_lines = HIDDEN_EXPECTED_PATH.read_bytes().splitlines()
        if not expected_lines:
            return 0.0

        build_env = {**os.environ, "CGO_ENABLED": "0"}
        with tempfile.TemporaryDirectory(dir="/tmp") as build_dir:
            binary = Path(build_dir) / "titlecase_app"
            for package in (".", "./..."):
                build = subprocess.run(
                    ["go", "build", "-o", str(binary), package],
                    cwd=repo_path,
                    env=build_env,
                    capture_output=True,
                    timeout=120,
                )
                if build.returncode == 0 and binary.is_file():
                    break
            else:
                return 0.0

            with tempfile.TemporaryDirectory(dir="/tmp") as jail_dir:
                jail = Path(jail_dir)
                jail.chmod(0o755)
                jailed_binary = jail / binary.name
                shutil.copyfile(binary, jailed_binary)
                jailed_binary.chmod(0o755)

                def enter_jail() -> None:
                    os.chroot(jail_dir)
                    os.chdir("/")
                    os.setgroups([])
                    os.setgid(65534)
                    os.setuid(65534)

                run = subprocess.run(
                    [f"/{binary.name}"],
                    input=hidden_inputs,
                    capture_output=True,
                    close_fds=True,
                    env={},
                    preexec_fn=enter_jail,
                    timeout=120,
                )
                if run.returncode != 0:
                    return 0.0
    except (OSError, subprocess.SubprocessError):
        return 0.0

    actual_lines = run.stdout.splitlines()
    matches = sum(
        actual == expected for actual, expected in zip(actual_lines, expected_lines)
    )
    return matches / max(len(actual_lines), len(expected_lines))

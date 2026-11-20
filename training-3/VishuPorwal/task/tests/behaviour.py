"""Score the share of hidden lines that match the original titlecase output."""

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from rewardkit import criterion

REPO = Path("/workspace/repo")
HIDDEN_INPUTS = Path("/tests/data/hidden_inputs.txt")
HIDDEN_EXPECTED = Path("/tests/data/hidden_expected.txt")
NOBODY = "65534:65534"
EXECUTION_TIMEOUT = 180


def _go_env() -> dict[str, str]:
    env = os.environ.copy()
    env["GOCACHE"] = tempfile.mkdtemp(prefix="go-cache-")
    env["CGO_ENABLED"] = "0"
    env["GOTOOLCHAIN"] = "local"
    return env


def _has_python(root: Path) -> bool:
    for path in root.rglob("*"):
        if path.is_file() and path.suffix == ".py":
            return True
    return False


def _build_passes() -> bool:
    try:
        result = subprocess.run(
            ["go", "build", "./..."],
            cwd=REPO,
            env=_go_env(),
            capture_output=True,
            timeout=EXECUTION_TIMEOUT,
        )
        return result.returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def _run_in_jail(jail: Path, binary_name: str, input_bytes: bytes) -> subprocess.CompletedProcess[bytes] | None:
    chroot_bin = shutil.which("chroot") or "/usr/sbin/chroot"
    if not os.path.exists(chroot_bin):
        print(f"Jail setup error: chroot binary not found at {chroot_bin}")
        return None
    try:
        proc = subprocess.run(
            [chroot_bin, f"--userspec={NOBODY}", "--groups=", str(jail), f"/{binary_name}"],
            input=input_bytes,
            capture_output=True,
            env={},
            cwd="/",
            close_fds=True,
            timeout=EXECUTION_TIMEOUT,
        )
        return proc
    except Exception as exc:
        print(f"Jail execution failure: {exc}")
        return None


@criterion
def behaviour(workspace: Path) -> float:
    del workspace
    if not REPO.is_dir() or not HIDDEN_INPUTS.is_file() or not HIDDEN_EXPECTED.is_file():
        return 0.0
    if not _build_passes() or _has_python(REPO):
        return 0.0

    try:
        expected = HIDDEN_EXPECTED.read_text(encoding="utf-8").splitlines()
        input_bytes = HIDDEN_INPUTS.read_bytes()
    except OSError as exc:
        print(f"Failed to read exam fixtures: {exc}")
        return 0.0

    if not expected:
        return 0.0

    jail_parent = Path(tempfile.mkdtemp(prefix="titlecase-jail-"))
    try:
        jail = jail_parent / "jail"
        jail.mkdir(mode=0o755)
        jail_parent.chmod(0o755)
        jail.chmod(0o755)
        binary = jail / "titlecase"

        # Build Go binary statically into jail directory
        build = subprocess.run(
            ["go", "build", "-o", str(binary), "."],
            cwd=REPO,
            env=_go_env(),
            capture_output=True,
            timeout=EXECUTION_TIMEOUT,
        )
        if build.returncode != 0 or not binary.is_file():
            return 0.0

        # Ensure executable is readable and traversable by runtime user, not writable
        binary.chmod(0o755)

        # Run inside isolated jail
        run = _run_in_jail(jail, "titlecase", input_bytes)
        if run is None or run.returncode != 0:
            return 0.0

        try:
            got = run.stdout.decode("utf-8").splitlines()
        except UnicodeDecodeError:
            return 0.0

        matches = sum(1 for i, line in enumerate(expected) if i < len(got) and got[i] == line)
        return matches / len(expected)
    except (OSError, subprocess.TimeoutExpired) as exc:
        print(f"Verifier execution error: {exc}")
        return 0.0
    finally:
        shutil.rmtree(jail_parent, ignore_errors=True)

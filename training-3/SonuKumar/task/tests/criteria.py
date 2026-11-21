import os
from pathlib import Path
import subprocess
import tempfile


REPO = Path("/workspace/repo")
INPUTS = Path("/tests/data/hidden_inputs.txt")
EXPECTED = Path("/tests/data/hidden_expected.txt")


def has_banned_imports() -> bool:
    try:
        res = subprocess.run(
            ["go", "list", "-f", "{{range .Imports}}{{.}} {{end}}", "./..."],
            cwd=REPO,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        banned = {"os/exec", "syscall", "syscall/js", "plugin"}
        return any(pkg in banned for pkg in res.stdout.split())
    except Exception:
        return True


def build() -> bool:
    result = subprocess.run(
        ["go", "build", "./..."],
        cwd=REPO,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return result.returncode == 0


def build_check(workspace: Path | None = None) -> float:
    if not REPO.is_dir():
        return 0.0
    return float(build())


def no_python_check(workspace: Path | None = None) -> float:
    if not REPO.is_dir():
        return 0.0
    no_python = not any(
        path.is_file() and path.suffix == ".py" for path in REPO.rglob("*")
    )
    if not no_python or not build() or has_banned_imports():
        return 0.0

    # Isolated smoke test: ensure the port actually performs Title Case logic,
    # preventing empty or echo-only programs (delete trick) from earning free points.
    with tempfile.TemporaryDirectory(dir="/tmp", prefix="tc-smoke-") as tmpdir:
        tmp_path = Path(tmpdir)
        tmp_path.chmod(0o755)
        smoke_bin = tmp_path / "titlecase-smoke"
        built = subprocess.run(
            ["go", "build", "-o", str(smoke_bin), "."],
            cwd=REPO,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if built.returncode != 0:
            return 0.0
        smoke_bin.chmod(0o755)

        clean_env = {
            "PATH": "/usr/bin:/bin",
            "TMPDIR": str(tmp_path),
            "HOME": str(tmp_path),
        }
        try:
            res = subprocess.run(
                [str(smoke_bin)],
                input=b"a tale of two cities\n",
                cwd=tmp_path,
                user="nobody",
                group="nogroup",
                env=clean_env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
                timeout=10,
            )
            if res.returncode != 0:
                return 0.0
            return float(res.stdout.strip() == b"A Tale of Two Cities")
        except (subprocess.TimeoutExpired, OSError, IOError):
            return 0.0


def behaviour_check(workspace: Path | None = None) -> float:
    if (
        not REPO.is_dir()
        or not (REPO / "go.mod").is_file()
        or not (REPO / "main.go").is_file()
    ):
        return 0.0

    with tempfile.TemporaryDirectory(dir="/tmp", prefix="tc-exec-") as tmpdir:
        tmp_path = Path(tmpdir)
        tmp_path.chmod(0o755)
        executable = tmp_path / "titlecase-go"
        built = subprocess.run(
            ["go", "build", "-o", str(executable), "."],
            cwd=REPO,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if built.returncode != 0:
            return 0.0
        executable.chmod(0o755)

        clean_env = {
            "PATH": "/usr/bin:/bin",
            "TMPDIR": str(tmp_path),
            "HOME": str(tmp_path),
        }
        try:
            result = subprocess.run(
                [str(executable)],
                input=INPUTS.read_bytes(),
                cwd=tmp_path,
                user="nobody",
                group="nogroup",
                env=clean_env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
                timeout=60,
            )
            if result.returncode != 0:
                return 0.0
            actual = result.stdout.splitlines()
            expected = EXPECTED.read_bytes().splitlines()
        except (subprocess.TimeoutExpired, OSError, IOError):
            return 0.0

    if not expected:
        return float(not actual)
    matching = sum(a == e for a, e in zip(actual, expected))
    accuracy = matching / max(len(actual), len(expected))
    return accuracy ** 2

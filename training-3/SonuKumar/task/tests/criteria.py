from pathlib import Path
import subprocess

from rewardkit import criterion


REPO = Path("/workspace/repo")
INPUTS = Path("/tests/data/hidden_inputs.txt")
EXPECTED = Path("/tests/data/hidden_expected.txt")


def build() -> bool:
    result = subprocess.run(
        ["go", "build", "./..."],
        cwd=REPO,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return result.returncode == 0


@criterion(description="go build ./... succeeds")
def build_check(workspace: Path) -> float:
    if not REPO.is_dir():
        return 0.0
    return float(build())


@criterion(description="no Python files remain and the Go project builds")
def no_python_check(workspace: Path) -> float:
    if not REPO.is_dir():
        return 0.0
    no_python = not any(
        path.is_file() and path.suffix == ".py" for path in REPO.rglob("*")
    )
    return float(no_python and build())


@criterion(description="hidden titlecase outputs match")
def behaviour_check(workspace: Path) -> float:
    if (
        not REPO.is_dir()
        or not (REPO / "go.mod").is_file()
        or not (REPO / "main.go").is_file()
    ):
        return 0.0
    executable = Path("/tmp/titlecase-go")
    built = subprocess.run(
        ["go", "build", "-o", str(executable), "."],
        cwd=REPO,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if built.returncode != 0:
        return 0.0

    try:
        result = subprocess.run(
            [str(executable)],
            input=INPUTS.read_bytes(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if result.returncode != 0:
            return 0.0
        actual = result.stdout.splitlines()
        expected = EXPECTED.read_bytes().splitlines()
    except (OSError, IOError):
        return 0.0

    if not expected:
        return float(not actual)
    matching = sum(a == e for a, e in zip(actual, expected))
    return matching / max(len(actual), len(expected))

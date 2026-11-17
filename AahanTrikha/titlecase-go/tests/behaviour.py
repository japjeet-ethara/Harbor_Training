import subprocess
from pathlib import Path

from rewardkit import criterion

REPO = Path("/workspace/repo")
DATA = Path("/tests/data")


@criterion
def behaviour(workspace: Path) -> float:
    try:
        build = subprocess.run(
            ["go", "build", "./..."], cwd=REPO,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False,
        )
        if build.returncode != 0:
            return 0.0
        binary = Path("/tmp/titlecase-go-verifier")
        built = subprocess.run(
            ["go", "build", "-o", str(binary), "."], cwd=REPO,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False,
        )
        if built.returncode != 0:
            return 0.0
        actual = subprocess.run(
            [str(binary)], cwd=REPO,
            input=(DATA / "hidden_inputs.txt").read_bytes(),
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False,
        )
        if actual.returncode != 0:
            return 0.0
        got = actual.stdout.splitlines(keepends=True)
        expected = (DATA / "hidden_expected.txt").read_bytes().splitlines(keepends=True)
        if not expected or len(got) != len(expected):
            return 0.0
        return sum(left == right for left, right in zip(got, expected)) / len(expected)
    except OSError:
        return 0.0

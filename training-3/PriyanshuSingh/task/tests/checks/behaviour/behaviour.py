"""behaviour: share of hidden titles whose output matches exactly."""
import os
import subprocess
import tempfile
from pathlib import Path

import rewardkit as rk

HIDDEN_INPUTS = Path("/tests/data/hidden_inputs.txt")
HIDDEN_EXPECTED = Path("/tests/data/hidden_expected.txt")
NOBODY = 65534


@rk.criterion(description="Share of hidden titles matching the original output")
def hidden_titles_match(workspace: Path) -> float:
    with tempfile.TemporaryDirectory() as folder:
        os.chmod(folder, 0o755)
        program = Path(folder) / "titlecase"
        build = subprocess.run(
            ["go", "build", "-o", str(program), "."],
            cwd=workspace,
            capture_output=True,
            timeout=300,
        )
        if build.returncode != 0:
            print(build.stderr.decode(errors="replace"))
            return 0.0

        # Split on \n only: titles may hold \x85,   and other characters
        # that str.splitlines() would treat as line ends.
        expected = HIDDEN_EXPECTED.read_bytes().split(b"\n")[:-1]
        try:
            with HIDDEN_INPUTS.open("rb") as titles:
                run = subprocess.run(
                    [str(program)],
                    stdin=titles,
                    capture_output=True,
                    cwd="/",
                    env={},
                    user=NOBODY,
                    group=NOBODY,
                    extra_groups=[],
                    timeout=120,
                )
        except subprocess.TimeoutExpired:
            return 0.0
        if run.returncode != 0:
            return 0.0

        actual = run.stdout.split(b"\n")
        matched = sum(got == want for got, want in zip(actual, expected))
        return matched / len(expected)

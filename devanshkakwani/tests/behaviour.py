from pathlib import Path
import subprocess
import tempfile

from rewardkit import Worker, WorkerError, WorkerSetupError, criterion


@criterion
def behaviour(workspace: Path) -> float:
    inputs = Path("/tests/data/hidden_inputs.txt").read_bytes()
    expected = Path("/tests/data/hidden_expected.txt").read_bytes().splitlines()

    with tempfile.TemporaryDirectory() as temp_dir:
        executable = Path(temp_dir) / "titlecase"
        build_result = subprocess.run(
            ["go", "build", "-o", str(executable), "."],
            cwd=workspace,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if build_result.returncode != 0:
            return 0.0

        executable.chmod(0o755)

        try:
            result = Worker().run(
                "./titlecase",
                files=[executable],
                stdin=inputs,
            )
        except WorkerSetupError:
            raise
        except WorkerError:
            return 0.0

    if result.returncode != 0:
        return 0.0

    actual = result.stdout.splitlines()
    denominator = max(len(expected), len(actual))
    if denominator == 0:
        return 1.0

    matches = sum(
        actual_line == expected_line
        for actual_line, expected_line in zip(actual, expected)
    )
    return matches / denominator

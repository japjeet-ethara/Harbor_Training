from pathlib import Path
import subprocess
import tempfile

from rewardkit import criterion


@criterion
def no_python(workspace: Path) -> bool:
    if any(workspace.rglob("*.py")):
        return False

    build = subprocess.run(
        ["go", "build", "./..."],
        cwd=workspace,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if build.returncode != 0:
        return False

    cases = (
        (b"hello from stdin\n", b"Hello From Stdin\n"),
        (b"the quick brown fox\n", b"The Quick Brown Fox\n"),
    )

    with tempfile.TemporaryDirectory() as temp_dir:
        executable = Path(temp_dir) / "titlecase"
        executable_build = subprocess.run(
            ["go", "build", "-o", str(executable), "."],
            cwd=workspace,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if executable_build.returncode != 0:
            return False

        for input_text, expected_output in cases:
            try:
                result = subprocess.run(
                    [str(executable)],
                    cwd=workspace,
                    input=input_text,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=False,
                    timeout=10,
                )
            except (OSError, subprocess.TimeoutExpired):
                return False
            if result.returncode != 0 or result.stdout != expected_output:
                return False

    return True

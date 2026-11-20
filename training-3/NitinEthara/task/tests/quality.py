"""Shared exact-suite gate for structural reward components."""
import subprocess
import tempfile
from pathlib import Path


DATA = Path(__file__).resolve().parent / "data"


def exact_exam_passes(workspace: Path) -> bool:
    input_path = DATA / "inputs.txt"
    answer_path = DATA / "answers.txt"
    if not input_path.is_file() or not answer_path.is_file():
        return False

    input_bytes = input_path.read_bytes()
    answer_bytes = answer_path.read_bytes()
    expected = answer_bytes.split(b"\n")
    if (
        len(input_bytes.split(b"\n")) != 100001
        or len(expected) != 100001
        or expected[-1] != b""
    ):
        return False
    expected.pop()

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            executable = Path(temp_dir) / "titlecase"
            build = subprocess.run(
                ["go", "build", "-o", str(executable), "."],
                cwd=workspace,
                capture_output=True,
                timeout=300,
            )
            if build.returncode != 0 or not executable.is_file():
                return False
            result = subprocess.run(
                [str(executable)],
                input=input_bytes,
                capture_output=True,
                timeout=120,
                cwd=temp_dir,
            )
    except (OSError, subprocess.TimeoutExpired):
        return False

    if result.returncode != 0:
        return False
    actual = result.stdout.split(b"\n")
    if not actual or actual[-1] != b"":
        return False
    return actual[:-1] == expected

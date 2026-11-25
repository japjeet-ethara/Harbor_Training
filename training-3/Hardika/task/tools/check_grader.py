import importlib.util
import json
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("titlecase_grader", ROOT / "tests/grade.py")
grader = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(grader)

CASES = {
    "nop": {"build": 0.0, "no_python": 0.0, "behaviour": 0.0},
    "oracle": {"build": 1.0, "no_python": 1.0, "behaviour": 1.0},
    "visible replay": {"build": 1.0, "no_python": 0.0, "behaviour": 0.0},
    "delete only": {"build": 0.0, "no_python": 0.0, "behaviour": 0.0},
    "clean replay": {"build": 1.0, "no_python": 1.0, "behaviour": 0.0},
}


def stage(workspace, variant):
    shutil.copytree(ROOT / "environment/upstream", workspace)
    if variant in {"oracle", "delete only", "clean replay"}:
        for python_file in workspace.rglob("*.py"):
            python_file.unlink()
    if variant == "oracle":
        for path in (ROOT / "solution/go").iterdir():
            if path.suffix in {".go", ".mod"}:
                shutil.copyfile(path, workspace / path.name)
    if variant in {"visible replay", "clean replay"}:
        for path in (ROOT / "cheat/replay").iterdir():
            shutil.copyfile(path, workspace / path.name)
        shutil.copyfile(ROOT / "tests/data/expected.txt", workspace / "visible-answers.txt")


def verify(go):
    assert grader.share_correct(b"a\nb\nc\n", [b"a", b"b", b"c"]) == 1.0
    assert grader.share_correct(b"a\nwrong\nc\n", [b"a", b"b", b"c"]) == 2 / 3
    assert grader.share_correct(b"a\nb\nc", [b"a", b"b", b"c"]) == 2 / 3
    assert grader.share_correct(b"a\nb\nc\nextra", [b"a", b"b", b"c"]) == 0
    assert grader.share_correct(b"a\nb\nc\n\n", [b"a", b"b", b"c"]) == 0
    assert grader.share_correct(b"a\r\nb\r\nc\r\n", [b"a", b"b", b"c"]) == 0
    assert grader.share_correct("a\u2028b\n\n".encode(), ["a\u2028b".encode(), b""]) == 1.0
    assert grader.share_correct(b"", [b"", b"b", b"c"]) == 0
    print("Exact byte comparison, blank output, partial output, and extra output checks passed",
          flush=True)
    for variant, expected in CASES.items():
        with tempfile.TemporaryDirectory(prefix="grader-fixture-") as directory:
            workspace = Path(directory) / "repo"
            stage(workspace, variant)
            actual = grader.grade(workspace, go, isolated=False)
            assert actual == expected, (variant, actual, expected)
            weighted = (actual["build"] + actual["no_python"] + 4 * actual["behaviour"]) / 6
            print(json.dumps({"fixture": variant, "checks": actual, "weighted": weighted}),
                  flush=True)


if __name__ == "__main__":
    verify(str(Path(sys.argv[1]).resolve()))

"""Grade the Go titlecase port against oracle datasets.

Visible cases also live at /workspace/visible_cases.json in the agent image.
Hidden cases are only in this tests directory.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

DATA = Path(__file__).resolve().parent / "data"
DRIVER = Path(__file__).resolve().parent / "driver" / "main.go"
MODULE_CANDIDATES = (
    Path("/workspace/titlecase"),
    Path("/logs/artifacts/workspace/titlecase"),
)


def _load(name):
    payload = json.loads((DATA / name).read_text(encoding="utf-8"))
    return payload["cases"]


VISIBLE = _load("visible.json")
HIDDEN = _load("hidden.json")


def _module_dir():
    override = os.environ.get("TITLECASE_MODULE")
    candidates = []
    if override:
        candidates.append(Path(override))
    candidates.extend(MODULE_CANDIDATES)
    for path in candidates:
        if (path / "go.mod").is_file():
            return path
    searched = ", ".join(str(path) for path in candidates)
    pytest.fail(f"Go module titlecase not found. Looked in: {searched}")


def _go_env(module):
    env = os.environ.copy()
    env["GOTOOLCHAIN"] = "local"
    env["CGO_ENABLED"] = "0"
    env["GOFLAGS"] = "-mod=mod"
    env["GOSUMDB"] = "off"
    return env


@pytest.fixture(scope="session")
def titlecase_bin(tmp_path_factory):
    module = _module_dir()
    work = tmp_path_factory.mktemp("titlecase-driver")
    module_path = module.resolve().as_posix()
    (work / "go.mod").write_text(
        "\n".join(
            [
                "module harborcheck",
                "",
                "go 1.23",
                "",
                "require titlecase v0.0.0",
                "",
                f"replace titlecase => {module_path}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    shutil.copy(DRIVER, work / "main.go")
    binary = work / "titlecase-driver"
    build = subprocess.run(
        ["go", "build", "-o", str(binary), "."],
        cwd=work,
        env=_go_env(module),
        text=True,
        capture_output=True,
        check=False,
    )
    if build.returncode != 0:
        pytest.fail(
            "go build of the titlecase driver failed:\n"
            + build.stdout
            + build.stderr
        )
    return binary


def _run(binary, case):
    payload = json.dumps(case)
    result = subprocess.run(
        [str(binary)],
        input=payload,
        text=True,
        encoding="utf-8",
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        pytest.fail(
            f"{case['id']} driver failed ({result.returncode}):\n"
            + result.stdout
            + result.stderr
        )
    try:
        output = json.loads(result.stdout)["output"]
    except (json.JSONDecodeError, KeyError) as exc:
        pytest.fail(f"{case['id']} driver returned {result.stdout!r} ({exc})")
    return output


def test_datasets_are_well_formed():
    assert VISIBLE, "visible dataset is empty"
    assert HIDDEN, "hidden dataset is empty"
    ids = [case["id"] for case in VISIBLE + HIDDEN]
    assert len(ids) == len(set(ids))
    for case in VISIBLE + HIDDEN:
        assert isinstance(case["text"], str)
        assert isinstance(case["expected"], str)
        assert case["id"]


@pytest.mark.parametrize("case", VISIBLE, ids=[case["id"] for case in VISIBLE])
def test_visible(titlecase_bin, case):
    assert _run(titlecase_bin, case) == case["expected"]


@pytest.mark.parametrize("case", HIDDEN, ids=[case["id"] for case in HIDDEN])
def test_hidden(titlecase_bin, case):
    assert _run(titlecase_bin, case) == case["expected"]

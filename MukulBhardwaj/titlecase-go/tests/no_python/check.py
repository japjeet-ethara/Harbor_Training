import http.client
import os
import subprocess
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

from rewardkit import criterion


RUNNER_URL = "http://runner:8080/run"
MAX_OUTPUT_BYTES = 64 * 1024 * 1024


def _first_lf_record(data: bytes) -> bytes:
    newline = data.find(b"\n")
    if newline == -1:
        return data
    return data[: newline + 1]


@criterion
def no_python_and_build_passes(workspace: Path) -> bool:
    if any(path.is_file() for path in workspace.rglob("*.py")):
        return False

    inputs_path = Path("/tests/data/inputs.txt")
    expected_path = Path("/tests/data/expected.txt")
    if not inputs_path.is_file() or not expected_path.is_file():
        return False

    public_input_data = inputs_path.read_bytes()
    public_expected_data = expected_path.read_bytes()
    if not public_input_data or not public_expected_data:
        return False

    public_input = _first_lf_record(public_input_data)
    public_expected = _first_lf_record(public_expected_data)
    token = os.environ.get("RUNNER_AUTH_TOKEN")
    if not token:
        return False

    try:
        result = subprocess.run(
            ["go", "build", "./..."],
            cwd=workspace,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=120,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    if result.returncode != 0:
        return False

    try:
        with tempfile.TemporaryDirectory(
            prefix="titlecase-smoke-", dir=workspace.resolve()
        ) as temp_dir:
            executable = Path(temp_dir) / "titlecase"
            build_env = os.environ.copy()
            build_env["CGO_ENABLED"] = "0"
            build = subprocess.run(
                ["go", "build", "-o", str(executable), "."],
                cwd=workspace.resolve(),
                env=build_env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=120,
                check=False,
            )
            if build.returncode != 0:
                return False

            request = urllib.request.Request(
                RUNNER_URL,
                data=public_input,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/octet-stream",
                    "X-Program-Path": str(executable),
                },
                method="POST",
            )
            deadline = time.monotonic() + 10
            while True:
                try:
                    with urllib.request.urlopen(request, timeout=70) as response:
                        if response.status != 200:
                            return False
                        exit_code = int(response.headers["X-Program-Exit-Code"])
                        actual = response.read(MAX_OUTPUT_BYTES + 1)
                        if len(actual) > MAX_OUTPUT_BYTES:
                            return False
                        return exit_code == 0 and actual == public_expected
                except urllib.error.HTTPError:
                    raise
                except urllib.error.URLError:
                    if time.monotonic() >= deadline:
                        raise
                    time.sleep(0.25)
    except (
        OSError,
        subprocess.TimeoutExpired,
        urllib.error.URLError,
        http.client.HTTPException,
        TimeoutError,
        ValueError,
        KeyError,
    ):
        return False

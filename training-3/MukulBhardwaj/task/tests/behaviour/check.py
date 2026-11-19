import http.client
import os
import subprocess
import tempfile
import urllib.error
import urllib.request
from pathlib import Path

from rewardkit import criterion


RUNNER_URL = "http://runner:8080/run"
MAX_OUTPUT_BYTES = 64 * 1024 * 1024


def _lf_records(data: bytes) -> list[bytes]:
    if not data:
        return []

    parts = data.split(b"\n")
    records = [part + b"\n" for part in parts[:-1]]
    if parts[-1]:
        records.append(parts[-1])
    return records


@criterion
def hidden_behavior_matches(workspace: Path) -> float:
    inputs_path = Path("/tests/data/hidden_inputs.txt")
    expected_path = Path("/tests/data/hidden_expected.txt")
    if not inputs_path.is_file() or not expected_path.is_file():
        return 0.0

    inputs = inputs_path.read_bytes()
    expected = _lf_records(expected_path.read_bytes())
    if not expected:
        return 0.0

    token = os.environ.get("RUNNER_AUTH_TOKEN")
    if not token:
        return 0.0

    try:
        with tempfile.TemporaryDirectory(
            prefix="titlecase-check-", dir=workspace.resolve()
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
                return 0.0

            request = urllib.request.Request(
                RUNNER_URL,
                data=inputs,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/octet-stream",
                    "X-Program-Path": str(executable),
                },
                method="POST",
            )
            with urllib.request.urlopen(request, timeout=70) as response:
                if response.status != 200:
                    return 0.0
                exit_code = int(response.headers["X-Program-Exit-Code"])
                actual_bytes = response.read(MAX_OUTPUT_BYTES + 1)
                if len(actual_bytes) > MAX_OUTPUT_BYTES:
                    return 0.0
    except (
        OSError,
        subprocess.TimeoutExpired,
        urllib.error.URLError,
        http.client.HTTPException,
        TimeoutError,
        ValueError,
        KeyError,
    ):
        return 0.0

    if exit_code != 0:
        return 0.0

    actual = _lf_records(actual_bytes)
    record_count = max(len(actual), len(expected))
    matches = sum(
        actual[index] == expected[index]
        for index in range(min(len(actual), len(expected)))
    )
    return matches / record_count

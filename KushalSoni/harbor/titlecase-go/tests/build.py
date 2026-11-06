"""Score 1 when `go build ./...` passes in the repository."""

import os
import subprocess
from pathlib import Path

from rewardkit import criterion


def go_env() -> dict[str, str]:
    env = os.environ.copy()
    env["PATH"] = "/usr/local/go/bin:" + env.get("PATH", "/usr/local/bin:/usr/bin:/bin")
    env.setdefault("GOTOOLCHAIN", "local")
    return env


def go_build_result(workspace: Path) -> tuple[bool, str]:
    if not workspace.is_dir():
        return False, f"missing {workspace}"
    try:
        result = subprocess.run(
            ["go", "build", "./..."],
            cwd=workspace,
            capture_output=True,
            timeout=180,
            check=False,
            env=go_env(),
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return False, str(exc)
    if result.returncode != 0:
        err = (result.stderr or result.stdout).decode("utf-8", "replace")[-800:]
        names = ", ".join(sorted(path.name for path in workspace.iterdir()))
        return False, f"files={names}\n{err}"
    return True, "ok"


@criterion
def build(workspace: Path) -> dict:
    ok, detail = go_build_result(workspace)
    return {"score": 1.0 if ok else 0.0, "reasoning": detail}

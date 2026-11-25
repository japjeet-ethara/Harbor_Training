from pathlib import Path
import subprocess
from rewardkit import criterion


@criterion(description="go build ./... passes and produces working titlecase output")
def go_build_passes(workspace: Path) -> bool:
    if not (workspace / "go.mod").is_file():
        return False

    result = subprocess.run(
        ["go", "build", "./..."],
        cwd=workspace,
        capture_output=True,
        text=True,
        timeout=120,
    )
    if result.returncode != 0:
        return False

    # Smoke test: verify that the binary actually titlecases input
    smoke_bin = Path("/tmp/smoke_titlecase_bin")
    build_smoke = subprocess.run(
        ["go", "build", "-o", str(smoke_bin), "."],
        cwd=workspace,
        capture_output=True,
        timeout=120,
    )
    if build_smoke.returncode != 0 or not smoke_bin.is_file():
        return False

    try:
        run_smoke = subprocess.run(
            [str(smoke_bin)],
            input=b"the lord of the rings\n",
            capture_output=True,
            timeout=10,
        )
        if run_smoke.returncode != 0:
            return False
        output = run_smoke.stdout.decode("utf-8", errors="replace").strip()
        return output == "The Lord of the Rings"
    finally:
        smoke_bin.unlink(missing_ok=True)

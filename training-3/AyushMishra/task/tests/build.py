import os
from pathlib import Path
import subprocess
import tempfile
from rewardkit import criterion

REPO_DIR = Path("/workspace/repo")


@criterion
def check_build(workspace: Path) -> float | dict[str, float | str]:
    repo_path = REPO_DIR if REPO_DIR.exists() else workspace
    try:
        with tempfile.TemporaryDirectory(dir="/tmp") as output_dir:
            result = subprocess.run(
                ["go", "build", "-o", output_dir + "/", "./..."],
                cwd=repo_path,
                env={**os.environ, "CGO_ENABLED": "0"},
                capture_output=True,
                text=True,
                timeout=120,
            )
        if result.returncode != 0:
            return {"score": 0.0, "reasoning": result.stderr.strip()}
        return 1.0
    except (OSError, subprocess.SubprocessError) as error:
        return {"score": 0.0, "reasoning": str(error)}

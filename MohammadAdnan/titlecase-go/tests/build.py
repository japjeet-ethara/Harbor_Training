from pathlib import Path
import subprocess
from rewardkit import criterion

@criterion
def build_passes(workspace: Path) -> bool:
    binary = workspace / "titlecase-check"
    result = subprocess.run(
        ["go", "build", "-o", str(binary), "./..."],
        cwd=workspace, capture_output=True, timeout=120
    )
    return result.returncode == 0

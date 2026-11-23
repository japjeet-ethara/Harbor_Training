import os
from pathlib import Path
import subprocess

from rewardkit import criterion

# Offline, no cgo, no toolchain download, no third-party modules.
GO_ENV = {
    **os.environ,
    "CGO_ENABLED": "0",
    "GOFLAGS": "-mod=mod",
    "GOPROXY": "off",
    "GOTOOLCHAIN": "local",
    "GOWORK": "off",
}


@criterion
def build(workspace: Path) -> bool:
    result = subprocess.run(
        ["go", "build", "./..."],
        cwd=workspace,
        env=GO_ENV,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=300,
    )
    return result.returncode == 0

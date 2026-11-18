"""Check 2 - no_python (weight 1).

Pays only if the repository still BUILDS *and* contains no `.py` file anywhere.
Requiring the build is deliberate: otherwise an agent that does nothing but
delete files would collect this point for free.
"""
import subprocess
import tempfile
from pathlib import Path

from rewardkit import criterion


@criterion(description="repository builds and no .py file remains anywhere under it")
def no_python(workspace: Path) -> bool:
    try:
        with tempfile.TemporaryDirectory() as out:  # see build.py for why -o dir/
            built = subprocess.run(["go", "build", "-o", out + "/", "./..."], cwd=workspace,
                                   capture_output=True, timeout=300).returncode == 0
    except (subprocess.TimeoutExpired, OSError):
        return False
    if not built:
        return False
    # rglob also walks hidden directories; compare the suffix case-insensitively.
    return not any(p.suffix.lower() == ".py" for p in workspace.rglob("*") if p.is_file() or p.is_symlink())

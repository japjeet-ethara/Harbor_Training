import importlib.util
import os
from pathlib import Path

from rewardkit import criterion

_spec = importlib.util.spec_from_file_location(
    "titlecase_go_worker", Path(__file__).resolve().parent / "go_worker.py"
)
_worker = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_worker)


def _has_python_file(root: Path) -> bool:
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        dirnames[:] = [name for name in dirnames if not os.path.islink(os.path.join(dirpath, name))]
        if any(name.endswith(".py") for name in filenames):
            return True
    return False


@criterion
def no_python(workspace: Path) -> bool:
    if not workspace.is_dir() or _has_python_file(workspace):
        return False
    result = _worker.run_go_or_fail(workspace, "/usr/local/go/bin/go build ./...")
    return result is not None and result.returncode == 0

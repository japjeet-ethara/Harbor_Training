import importlib.util
from pathlib import Path

from rewardkit import criterion

_spec = importlib.util.spec_from_file_location(
    "titlecase_go_worker", Path(__file__).resolve().parent / "go_worker.py"
)
_worker = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_worker)


@criterion
def build(workspace: Path) -> bool:
    result = _worker.run_go_or_fail(workspace, "/usr/local/go/bin/go build ./...")
    return result is not None and result.returncode == 0

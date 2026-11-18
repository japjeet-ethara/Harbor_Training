import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from rewardkit import Worker, WorkerError, criterion

from grader_support import GO_ENV, build_command


@criterion
def module_builds(workspace: Path) -> bool:
    if not workspace.is_dir():
        return False
    try:
        result = Worker(env=GO_ENV).run(
            build_command(workspace),
            files=[workspace],
            timeout_sec=180,
        )
    except WorkerError:
        return False
    return result.returncode == 0

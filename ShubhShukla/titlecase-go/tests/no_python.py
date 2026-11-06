import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from rewardkit import Worker, WorkerError, criterion

from grader_support import GO_ENV, build_command, contains_python_file


@criterion
def no_python_sources(workspace: Path) -> bool:
    try:
        if not workspace.is_dir() or contains_python_file(workspace):
            return False
    except OSError:
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

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from rewardkit import Worker, WorkerError, criterion

from grader_support import (
    GO_ENV,
    HIDDEN_EXPECTED,
    HIDDEN_INPUT,
    require_dataset,
    run_command,
    stdout_matches,
)


def _matches(workspace: Path, source: Path, expected: Path) -> bool:
    try:
        result = Worker(env=GO_ENV).run(
            run_command(workspace),
            files=[workspace],
            stdin=require_dataset(source),
            timeout_sec=180,
        )
    except WorkerError:
        return False
    return result.returncode == 0 and stdout_matches(result.stdout, expected)


@criterion
def exact_titlecase_output(workspace: Path) -> bool:
    if not workspace.is_dir():
        return False
    return _matches(workspace, HIDDEN_INPUT, HIDDEN_EXPECTED)

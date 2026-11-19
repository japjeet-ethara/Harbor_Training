import importlib.util
from pathlib import Path

try:
    from rewardkit import criterion
except ImportError:
    def criterion(func=None, **kwargs):
        if callable(func):
            return func
        def decorator(f):
            return f
        return decorator


def _runner():
    path = Path(__file__).resolve().parent / "port_runner.py"
    spec = importlib.util.spec_from_file_location("titlecase_port_runner", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@criterion
def behaviour(workspace: Path = Path("/workspace/repo")) -> float:
    """3. behaviour (weight 4): build the Go program, run it alone in an empty chroot
    jail as user nobody, feed it tests/data/hidden_inputs.txt and compare with
    tests/data/hidden_expected.txt (held only in the grader's memory).
    Score 0 below 80% exact lines, then linear up to 1.0 at 100%.
    """
    runner = _runner()
    return float(runner.graded(runner.hidden_accuracy(runner.repo_dir(workspace))))


if __name__ == "__main__":
    print(behaviour())

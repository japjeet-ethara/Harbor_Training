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
def no_python(workspace: Path = Path("/workspace/repo")) -> float:
    """2. no_python (weight 1): 1 only if ALL hold:
    - `go build ./...` passes,
    - no .py file, no Python source under another name, no Go file importing os/exec,
    - the Go port really works: the jailed binary gets at least 80% of the hidden
      lines exactly right (deleting the Python files alone earns nothing).
    """
    runner = _runner()
    repo = runner.repo_dir(workspace)
    if not repo.exists() or not runner.go_build_all(repo):
        return 0.0
    if runner.python_left_in_repo(repo):
        return 0.0
    if runner.hidden_accuracy(repo) < runner.PASS_MARK:
        return 0.0
    return 1.0


if __name__ == "__main__":
    print(no_python())

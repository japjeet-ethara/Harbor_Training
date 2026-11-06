import subprocess
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


@criterion
def no_python(workspace: Path = Path("/workspace/repo")) -> float:
    """2. no_python (weight 1): no .py files anywhere under /workspace/repo AND the build passes -> 1, else 0."""
    repo_dir = Path("/workspace/repo")
    if not repo_dir.exists() and workspace and Path(workspace).exists():
        repo_dir = Path(workspace)

    if not repo_dir.exists():
        return 0.0

    # 1. Check that go build ./... passes
    try:
        res = subprocess.run(
            ["go", "build", "./..."],
            cwd=str(repo_dir),
            capture_output=True,
            text=True,
            timeout=120,
        )
        if res.returncode != 0:
            return 0.0
    except Exception:
        return 0.0

    # 2. Check that no .py files exist anywhere under repo_dir
    py_files = list(repo_dir.rglob("*.py"))
    if len(py_files) > 0:
        return 0.0

    return 1.0


if __name__ == "__main__":
    print(no_python())

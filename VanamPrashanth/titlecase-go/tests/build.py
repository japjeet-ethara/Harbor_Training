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
def build(workspace: Path = Path("/workspace/repo")) -> float:
    """1. build (weight 1): `go build ./...` in /workspace/repo passes -> 1, else 0."""
    repo_dir = Path("/workspace/repo")
    if not repo_dir.exists() and workspace and Path(workspace).exists():
        repo_dir = Path(workspace)

    if not repo_dir.exists():
        return 0.0

    try:
        res = subprocess.run(
            ["go", "build", "./..."],
            cwd=str(repo_dir),
            capture_output=True,
            text=True,
            timeout=120,
        )
        return 1.0 if res.returncode == 0 else 0.0
    except Exception:
        return 0.0


if __name__ == "__main__":
    print(build())

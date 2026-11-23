"""
Criterion 1: build (weight 1)
Run `go build ./...` inside `/workspace/repo`.
Score 1 if it succeeds, otherwise 0.
"""

import subprocess
from pathlib import Path

try:
    from rewardkit import criterion
except ImportError:
    def criterion(fn):
        return fn


@criterion
def check_build(workspace: Path) -> float:
    try:
        res = subprocess.run(
            ["go", "build", "./..."],
            cwd=str(workspace),
            capture_output=True,
            timeout=120,
        )
        if res.returncode != 0:
            return 0.0

        # Verify the binary is executable and performs basic titlecase logic
        # Blocks empty stubs and non-functioning programs (Cheat 3)
        tmp_smoke = workspace / "_smoke_build_bin"
        try:
            build_res = subprocess.run(
                ["go", "build", "-o", str(tmp_smoke), "."],
                cwd=str(workspace),
                capture_output=True,
                timeout=60,
            )
            if build_res.returncode != 0:
                return 0.0
            run_res = subprocess.run(
                [str(tmp_smoke)],
                input=b"a tale of two cities\n",
                cwd=str(workspace),
                capture_output=True,
                timeout=10,
            )
            if run_res.returncode != 0 or run_res.stdout.strip() != b"A Tale of Two Cities":
                return 0.0
        finally:
            if tmp_smoke.exists():
                try:
                    tmp_smoke.unlink()
                except Exception:
                    pass

        return 1.0
    except Exception:
        return 0.0


if __name__ == "__main__":
    import sys
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace/repo")
    print(check_build(target))

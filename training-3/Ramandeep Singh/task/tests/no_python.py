"""
Criterion 2: no_python (weight 1)
Check that no .py files remain anywhere under /workspace/repo,
AND the Go build succeeds. Score 1 if both conditions are satisfied, otherwise 0.
"""

import subprocess
from pathlib import Path

try:
    from rewardkit import criterion
except ImportError:
    def criterion(fn):
        return fn


@criterion
def check_no_python(workspace: Path) -> float:
    try:
        # 1. Check that no .py or .pyc files exist anywhere under workspace (case-insensitive)
        banned_files = [
            p for p in workspace.rglob("*")
            if p.is_file() and (p.name.lower().endswith(".py") or p.name.lower().endswith(".pyc"))
        ]
        if banned_files:
            return 0.0

        # 2. Check for cloaked Python source files (e.g. reference.txt)
        py_signatures = ["def titlecase(", "REGEX_AVAILABLE", "import regex", "exec(open("]
        for p in workspace.rglob("*"):
            if p.is_file() and not p.name.startswith(".") and p.suffix not in {".go", ".mod", ".sum", ".md", ".png", ".toml"}:
                try:
                    content = p.read_text(encoding="utf-8", errors="ignore")
                    if any(sig in content for sig in py_signatures):
                        return 0.0
                except Exception:
                    pass

        # 3. Ban subprocess/system execution imports (candidate must be pure Go)
        import_res = subprocess.run(
            ["go", "list", "-f", "{{range .Imports}}{{.}} {{end}}", "./..."],
            cwd=str(workspace),
            capture_output=True,
            text=True,
            timeout=60,
        )
        if import_res.returncode == 0:
            banned_imports = {"os/exec", "syscall", "syscall/js", "plugin", "unsafe"}
            imported = set(import_res.stdout.split())
            if banned_imports & imported:
                return 0.0

        # 4. Check that Go build succeeds
        res = subprocess.run(
            ["go", "build", "./..."],
            cwd=str(workspace),
            capture_output=True,
            timeout=120,
        )
        if res.returncode != 0:
            return 0.0

        # 5. Smoke test: ensure the port actually performs titlecase transformations
        # Blocks empty stubs and echo programs (Cheat 3) from earning unearned marks
        tmp_smoke = workspace / "_smoke_test_bin"
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
    print(check_no_python(target))

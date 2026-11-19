from pathlib import Path
import subprocess
from rewardkit import criterion


@criterion(description="no python files or embedded python code remain under /workspace/repo")
def no_python_and_builds(workspace: Path) -> bool:
    # 1. No python extension files
    for p in workspace.rglob("*"):
        if p.is_file() and p.suffix.lower() in {".py", ".pyc", ".pyo", ".pyd", ".pyw"}:
            return False

    # 2. Check for embedded python source or scripts
    python_signatures = [
        b"def titlecase",
        b"import regex",
        b"import re",
        b"os.environ[\"TC_SRC\"]",
        b"titlecase_embedded",
        b"exec(compile(",
        b"/usr/bin/python",
    ]
    for p in workspace.rglob("*"):
        if p.is_file() and not p.name.startswith("."):
            try:
                content = p.read_bytes()
                for sig in python_signatures:
                    if sig in content:
                        return False
            except Exception:
                pass

    # 3. Clean build passes and produces valid titlecase output
    if not (workspace / "go.mod").is_file():
        return False

    result = subprocess.run(
        ["go", "build", "./..."],
        cwd=workspace,
        capture_output=True,
        text=True,
        timeout=120,
    )
    if result.returncode != 0:
        return False

    smoke_bin = Path("/tmp/no_py_smoke_bin")
    build_smoke = subprocess.run(
        ["go", "build", "-o", str(smoke_bin), "."],
        cwd=workspace,
        capture_output=True,
        timeout=120,
    )
    if build_smoke.returncode != 0 or not smoke_bin.is_file():
        return False

    try:
        run_smoke = subprocess.run(
            [str(smoke_bin)],
            input=b"the lord of the rings\n",
            capture_output=True,
            timeout=10,
        )
        if run_smoke.returncode != 0:
            return False
        output = run_smoke.stdout.decode("utf-8", errors="replace").strip()
        return output == "The Lord of the Rings"
    finally:
        smoke_bin.unlink(missing_ok=True)

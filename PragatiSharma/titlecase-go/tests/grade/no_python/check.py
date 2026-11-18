import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from rewardkit import criterion

from support import go_build_all, log


@criterion
def no_python(workspace: Path) -> dict[str, object]:
    ok, detail = go_build_all(workspace)
    if not ok:
        log(f"no_python: build failed: {detail}")
        return {"score": False, "reasoning": f"build failed: {detail}"}

    if not workspace.is_dir():
        return {"score": False, "reasoning": "workspace is missing"}

    python_files = sorted(
        path for path in workspace.rglob("*") if path.is_file() and path.suffix == ".py"
    )
    if python_files:
        shown = ", ".join(str(path) for path in python_files[:10])
        reason = f"found {len(python_files)} .py file(s): {shown}"
        log(f"no_python: {reason}")
        return {"score": False, "reasoning": reason}

    log("no_python: build succeeded and no .py files remain")
    return {"score": True, "reasoning": "build succeeded and no .py files remain"}

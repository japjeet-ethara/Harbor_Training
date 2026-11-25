import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from rewardkit import criterion

from support import go_build_all, log, python_files


@criterion
def no_python(workspace: Path) -> dict[str, object]:
    ok, detail = go_build_all(workspace)
    if not ok:
        log(f"no_python: build failed: {detail}")
        return {"score": False, "reasoning": f"build failed: {detail}"}

    if not workspace.is_dir():
        return {"score": False, "reasoning": "workspace is missing"}

    found = python_files(workspace)
    if found:
        shown = ", ".join(str(path) for path in found[:10])
        reason = f"found {len(found)} .py file(s): {shown}"
        log(f"no_python: {reason}")
        return {"score": False, "reasoning": reason}

    log("no_python: build succeeded and no .py files remain")
    return {"score": True, "reasoning": "build succeeded and no .py files remain"}

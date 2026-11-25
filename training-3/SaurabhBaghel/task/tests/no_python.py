"""No Python sources remain, and the Go module still builds.

Python source copied to a different extension must not bypass this check.
"""

import ast
import sys
from pathlib import Path

from rewardkit import criterion

sys.path.insert(0, str(Path(__file__).resolve().parent))
from support import go_build  # noqa: E402


def contains_python_source(path: Path) -> bool:
    if path.suffix.lower() in {".py", ".pyc", ".pyo"}:
        return True

    try:
        source = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return False

    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError:
        return False

    nodes = tuple(ast.walk(tree))
    has_import = any(isinstance(node, (ast.Import, ast.ImportFrom)) for node in nodes)
    has_definition = any(
        isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
        for node in nodes
    )
    has_dynamic_execution = any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id in {"eval", "exec"}
        for node in nodes
    )
    return has_import and (has_definition or has_dynamic_execution)


@criterion
def no_python(workspace: Path) -> float:
    try:
        if not workspace.is_dir():
            return 0.0
        if any(contains_python_source(path) for path in workspace.rglob("*") if path.is_file()):
            return 0.0
        result = go_build(workspace, "./...")
        return 1.0 if result.returncode == 0 else 0.0
    except Exception:
        return 0.0

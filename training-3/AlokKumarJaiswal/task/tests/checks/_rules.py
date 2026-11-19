"""Helper checks. This module registers no Reward Kit criteria."""

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

_FORBIDDEN = {"os/exec", "syscall", "plugin", "unsafe", "C", "net"}
_LIST_FORMAT = (
    '{{.ImportPath}} {{join .Imports " "}} {{join .TestImports " "}} '
    '{{join .XTestImports " "}}'
)
_DIRECTIVES = ("require", "replace", "use")


def build_binary(workspace: Path) -> bool:
    try:
        result = subprocess.run(
            ["go", "build", "-o", "/tmp/titlecase_bin", "."],
            cwd=workspace,
            capture_output=True,
            timeout=240,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return result.returncode == 0


def _forbidden(path: str) -> bool:
    return path in _FORBIDDEN or path.startswith("net/")


def _read_gomod(workspace: Path) -> str | None:
    try:
        return (workspace / "go.mod").read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return None


def _module_path(text: str) -> str | None:
    for raw in text.splitlines():
        code = raw.split("//", 1)[0].strip()
        parts = code.split()
        if len(parts) >= 2 and parts[0] == "module":
            return parts[1].strip('"')
    return None


def _directives_ok(text: str) -> bool:
    for raw in text.splitlines():
        code = raw.split("//", 1)[0].strip()
        if not code:
            continue
        for word in _DIRECTIVES:
            if code.startswith(word) and (
                len(code) == len(word) or code[len(word)] in " \t("
            ):
                return False
    return True


def _listed_imports(workspace: Path) -> set[str] | None:
    try:
        result = subprocess.run(
            ["go", "list", "-e", "-f", _LIST_FORMAT, "./..."],
            cwd=workspace,
            capture_output=True,
            timeout=60,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    imports: set[str] = set()
    for line in result.stdout.decode("utf-8", "replace").splitlines():
        parts = line.split()
        imports.update(parts[1:])
    return imports


def _standard_flags(workspace: Path, imports: set[str]) -> dict[str, bool] | None:
    try:
        result = subprocess.run(
            [
                "go",
                "list",
                "-e",
                "-f",
                "{{.ImportPath}} {{.Standard}}",
                *sorted(imports),
            ],
            cwd=workspace,
            capture_output=True,
            timeout=60,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    flags: dict[str, bool] = {}
    for line in result.stdout.decode("utf-8", "replace").splitlines():
        parts = line.split()
        if len(parts) == 2:
            flags[parts[0]] = parts[1] == "true"
    return flags


def _allowed(path: str, standard: dict[str, bool], module: str | None) -> bool:
    if standard.get(path) is True:
        return True
    return module is not None and (path == module or path.startswith(module + "/"))


def rules_ok(workspace: Path) -> bool:
    imports = _listed_imports(workspace)
    if imports is None or any(_forbidden(path) for path in imports):
        return False
    gomod = _read_gomod(workspace)
    if gomod is None or not _directives_ok(gomod):
        return False
    if not imports:
        return True
    standard = _standard_flags(workspace, imports)
    if standard is None:
        return False
    module = _module_path(gomod)
    return all(_allowed(path, standard, module) for path in imports)


def run_jailed(input_bytes: bytes) -> bytes | None:
    try:
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as jail:
            os.chmod(jail, 0o755)
            dest = os.path.join(jail, "titlecase_bin")
            shutil.copyfile("/tmp/titlecase_bin", dest)
            os.chmod(dest, 0o755)
            result = subprocess.run(
                ["chroot", "--userspec=65534:65534", jail, "/titlecase_bin"],
                input=input_bytes,
                capture_output=True,
                timeout=60,
            )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    return result.stdout

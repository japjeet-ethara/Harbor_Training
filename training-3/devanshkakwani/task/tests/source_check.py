"""Gate: the workspace holds a pure-Go, standard-library port and nothing else that runs.

Replaces the old `no_python` check, which only looked for files named *.py
(Sakshi Singh's cheat 2 renamed the Python source and passed it).

Rejected:
  * Python files of any kind (.py/.pyc/...) and native objects (.so/.a/.syso).
  * Go code that can start another program or reach past the Go runtime:
    imports of os/exec, syscall, plugin, unsafe, golang.org/x/sys, cgo ("C"),
    the identifiers StartProcess/ProcAttr, and //go:embed, //go:linkname,
    //go:cgo_* directives (embed would let a lookup table or a script ride along).
  * Any dependency outside the standard library and the main module.
  * More than MAX_GO_SOURCE_BYTES of Go source (a lookup table in disguise),
    or any non-Go file over MAX_OTHER_FILE_BYTES. ELF executables are exempt:
    `go build ./...` leaves one in the repo, and the binary under test cannot
    read the workspace (see behaviour.py), so a file there cannot feed it data.
"""

import json
import os
import re
import subprocess
from pathlib import Path

from rewardkit import criterion

GO_ENV = {
    **os.environ,
    "CGO_ENABLED": "0",
    "GOFLAGS": "-mod=mod",
    "GOPROXY": "off",
    "GOTOOLCHAIN": "local",
    "GOWORK": "off",
}

MAX_GO_SOURCE_BYTES = 256 * 1024  # whole tree; the reference port is 13 KiB
MAX_OTHER_FILE_BYTES = 64 * 1024  # per file; NOTES.md, the largest kept file, is 12 KiB

BANNED_SUFFIXES = {".py", ".pyc", ".pyo", ".pyw", ".pyz", ".so", ".a", ".syso"}
BANNED_IMPORTS = {"os/exec", "syscall", "plugin", "unsafe", "C", "runtime/cgo"}
BANNED_IMPORT_PREFIXES = ("golang.org/x/sys/", "internal/")

_IMPORT_SINGLE = re.compile(r'^\s*import\s+(?:[\w.]+\s+)?["`]([^"`\n]+)["`]', re.MULTILINE)
_IMPORT_BLOCK = re.compile(r"^\s*import\s*\((.*?)\)", re.MULTILINE | re.DOTALL)
_QUOTED = re.compile(r'["`]([^"`\n]+)["`]')
BANNED_TEXT = (
    re.compile(r"//\s*go:(embed|linkname|cgo_\w+)\b"),
    re.compile(r"\b(StartProcess|ProcAttr)\b"),
    re.compile(r"^\s*#\s*cgo\b", re.MULTILINE),
)


def _banned_import(path: str) -> bool:
    return path in BANNED_IMPORTS or path.startswith(BANNED_IMPORT_PREFIXES)


def _files(workspace: Path):
    for root, dirs, files in os.walk(workspace, followlinks=False):
        dirs[:] = [d for d in dirs if d != ".git"]
        for name in files:
            yield Path(root) / name


def _scan_files(workspace: Path) -> bool:
    go_bytes = 0
    for path in _files(workspace):
        info = path.lstat()
        if path.suffix.lower() in BANNED_SUFFIXES:
            return False
        if path.suffix == ".go":
            go_bytes += info.st_size
            if go_bytes > MAX_GO_SOURCE_BYTES:
                return False
            text = path.read_text(encoding="utf-8", errors="replace")
            if any(p.search(text) for p in BANNED_TEXT):
                return False
            # Text scan of every .go file, so files excluded by build tags or
            # CGO_ENABLED=0 (which `go list` does not parse) are covered too.
            imports = _IMPORT_SINGLE.findall(text)
            for block in _IMPORT_BLOCK.findall(text):
                imports += _QUOTED.findall(block)
            if any(_banned_import(i) for i in imports):
                return False
            continue
        if info.st_size > MAX_OTHER_FILE_BYTES:
            with open(path, "rb") as f:
                if f.read(4) != b"\x7fELF":
                    return False
    return go_bytes > 0


def _go_packages(workspace: Path):
    result = subprocess.run(
        ["go", "list", "-deps", "-json", "./..."],
        cwd=workspace,
        env=GO_ENV,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=300,
    )
    if result.returncode != 0:
        return None
    decoder, text, pos, packages = json.JSONDecoder(), result.stdout.decode(), 0, []
    while pos < len(text):
        while pos < len(text) and text[pos].isspace():
            pos += 1
        if pos == len(text):
            break
        package, pos = decoder.raw_decode(text, pos)
        packages.append(package)
    return packages


@criterion
def source_check(workspace: Path) -> bool:
    if not _scan_files(workspace):
        return False
    packages = _go_packages(workspace)
    if not packages:
        return False
    for package in packages:
        if package.get("Standard"):
            continue
        if not (package.get("Module") or {}).get("Main"):
            return False  # third-party or vendored dependency
        if package.get("CgoFiles") or package.get("EmbedPatterns"):
            return False
        if any(_banned_import(p) for p in package.get("Imports", [])):
            return False
    return True

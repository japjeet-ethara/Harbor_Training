"""Shared helpers for the three checks (this file defines no criterion of its own).

rules_ok()  - the hard rules from instruction.md, checked statically on the source.
go_build()  - `go build` with the network off and only the local toolchain.

Both run as root on the agent's files but never execute them: `go list` and
`go build` do not run user code when cgo is disabled.
"""
import json
import os
import re
import subprocess
from pathlib import Path

GO_ENV = dict(os.environ, GOFLAGS="-mod=readonly", GOPROXY="off", GOWORK="off",
              GOTOOLCHAIN="local", GOCACHE="/tmp/gocache-verifier", CGO_ENABLED="0")

# Packages that let a program start other programs (e.g. a hidden Python) or
# escape the standard library rules, when imported by the agent's own code.
FORBIDDEN_IMPORTS = {"os/exec", "syscall", "unsafe", "plugin", "C", "runtime/cgo"}
# ...and anywhere in the dependency tree: standard packages such as net/http/cgi
# or go/build start programs through os/exec internally.
FORBIDDEN_DEPS = {"os/exec", "plugin", "runtime/cgo"}
# os.StartProcess lives in package "os", which every port needs, so the name itself
# is banned. go:linkname needs "unsafe", which is banned above.
FORBIDDEN_SOURCE = re.compile(r"StartProcess|ForkExec|go:linkname|go:cgo_")
# Files `go build` would compile or link that are not Go source.
NON_GO_SOURCES = (".s", ".S", ".sx", ".c", ".cc", ".cpp", ".cxx", ".h", ".hh", ".hpp",
                  ".hxx", ".m", ".f", ".F", ".for", ".f90", ".swig", ".swigcxx", ".syso")


def rules_ok(workspace: Path) -> tuple[bool, str]:
    """(passed, reason). Python gone, stdlib only, no cgo, no starting programs."""
    gomod = workspace / "go.mod"
    if not gomod.is_file() or gomod.is_symlink():
        return False, "no go.mod"
    if re.search(r"^\s*(require|replace)\b", gomod.read_text(errors="replace"), re.M):
        return False, "go.mod has require/replace (third-party modules)"

    go_files = []
    for root, dirs, files in os.walk(workspace):
        for name in dirs + files:
            p = Path(root) / name
            if p.is_symlink():
                return False, f"symbolic link {p}"
        for name in files:
            if name.endswith(".py"):
                return False, f"Python file {name}"
            if name.endswith(NON_GO_SOURCES):
                return False, f"non-Go source file {name}"
            if name.endswith(".go"):
                go_files.append(Path(root) / name)
    if not go_files:
        return False, "no Go files"
    for f in go_files:
        if FORBIDDEN_SOURCE.search(f.read_text(encoding="utf-8", errors="replace")):
            return False, f"forbidden identifier in {f.name}"

    try:
        r = subprocess.run(["go", "list", "-deps", "-json", "./..."], cwd=workspace,
                           env=GO_ENV, capture_output=True, timeout=120)
    except (subprocess.TimeoutExpired, OSError):
        return False, "go list failed"
    if r.returncode != 0:
        return False, "go list failed"
    decoder, text, i = json.JSONDecoder(), r.stdout.decode(errors="replace"), 0
    while i < len(text):
        while i < len(text) and text[i].isspace():
            i += 1
        if i >= len(text):
            break
        pkg, i = decoder.raw_decode(text, i)
        if pkg.get("Error"):
            return False, f"package error in {pkg.get('ImportPath')}"
        if pkg.get("ImportPath") in FORBIDDEN_DEPS:
            return False, f"depends on {pkg.get('ImportPath')}"
        main_module = (pkg.get("Module") or {}).get("Main", False)
        if not pkg.get("Standard") and not main_module:
            return False, f"non-standard package {pkg.get('ImportPath')}"
        if main_module:
            bad = FORBIDDEN_IMPORTS & set(pkg.get("Imports") or [])
            if bad:
                return False, f"forbidden import {sorted(bad)[0]}"
    return True, "ok"


def go_build(workspace: Path, output: str, target: str) -> bool:
    if not (workspace / "go.mod").is_file():
        return False
    try:
        r = subprocess.run(["go", "build", "-o", output, target], cwd=workspace, env=GO_ENV,
                           capture_output=True, timeout=240)
    except (subprocess.TimeoutExpired, OSError):
        return False
    return r.returncode == 0

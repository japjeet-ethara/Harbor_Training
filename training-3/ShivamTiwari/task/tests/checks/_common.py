"""Shared compliance audit and exam runner used by every criterion.

A submission must satisfy the structural rules before *any* criterion can pay
out. `build`, `no_python` and `behaviour` all call `audit()` and `exam()`, so a
correct implementation that also smuggles a runtime, an assembly file, a
vendored module or a network oracle scores zero everywhere instead of keeping
two thirds of the reward.

The point is deliberate: the earlier design enforced the rules only inside
`no_python`, which let a submission pair perfect behaviour with a structural
violation and still collect 5/6.
"""

import os
import pwd
import re
import subprocess
from pathlib import Path

DATA = Path("/tests/data")
GO = "/usr/local/go/bin/go"
MIN_ACCURACY = 0.98

BUILD_ENV = {
    "PATH": "/usr/local/go/bin:/usr/bin:/bin",
    "HOME": "/root",
    "GO111MODULE": "on",
    "GOTOOLCHAIN": "local",
    "GOWORK": "off",
    "GOPROXY": "off",
    "GOFLAGS": "-mod=mod",
    "CGO_ENABLED": "0",
}
RUN_ENV = {"PATH": "/usr/bin:/bin", "CGO_ENABLED": "0"}

BANNED_SUFFIXES = {
    # Python
    ".py", ".pyc", ".pyo", ".pyd", ".pyw",
    # native objects, assembly and foreign source
    ".s", ".syso", ".o", ".a", ".so", ".dylib", ".dll",
    ".c", ".h", ".cc", ".cp", ".cpp", ".cxx", ".m", ".wasm",
    # other language runtimes
    ".js", ".mjs", ".pl", ".rb", ".php", ".lua", ".class", ".jar",
}
BANNED_IMPORT = re.compile(
    r'["`](?:os/exec|syscall|plugin|unsafe|net(?:/[^"`]*)?|'
    r'golang\.org/x/(?:sys|net)[^"`]*)[`"]'
)
# Import paths that a titlecase port never needs. The first set is checked on
# direct imports only, because the standard library itself pulls in `unsafe`
# and `syscall`; the second set is safe to check transitively because `os`,
# `strings`, `unicode`, `regexp` and friends never reach them.
BANNED_DIRECT_IMPORTS = {
    "C", "os/exec", "syscall", "plugin", "unsafe", "net", "embed", "runtime/cgo",
}
BANNED_DEP_IMPORTS = {"os/exec", "plugin", "embed", "runtime/cgo", "net"}
BANNED_IMPORT_PREFIXES = ("net/", "golang.org/x/sys/", "golang.org/x/net/")
BANNED_TOKEN = (
    "//go:embed",
    "//go:linkname",
    'import "C"',
    # Symbol names, not qualified calls: a package alias such as
    # `import o "os"; o.StartProcess(...)` must not hide them.
    "StartProcess",
    "ProcAttr",
    "exec.Command",
    "exec.Cmd",
    "exec.LookPath",
    "plugin.Open",
    "syscall.Exec",
    "syscall.ForkExec",
    "syscall.StartProcess",
    "syscall.RawSyscall",
    "syscall.Syscall",
)
GO_MOD_DIRECTIVE = re.compile(r"(?m)^\s*(?:require|replace|toolchain)\b")
# Byte signatures of a Python runtime or of Python source.
RUNTIME_MARKERS = (
    b"Py_Initialize",
    b"Py_Finalize",
    b"PyImport_",
    b"PyInit_",
    b"libpython",
    b"/usr/lib/python",
    b"/usr/local/lib/python",
    b"def titlecase(",
)
SKIP_DIRS = {".git"}


def _go_imports(workspace: Path):
    """Return (local packages -> direct imports, transitive imports).

    The source regex is only a first pass: Go also accepts raw-string and
    escaped import paths such as ``import `os/exec` `` or
    ``import "os\x2fexec"``, and a hidden ``_pkg`` directory is skipped by
    ``./...``. The module graph is therefore the authoritative check: every
    reachable package that belongs to the submitted module has its direct
    imports inspected, including packages the wildcard does not list.
    """
    common = dict(
        cwd=workspace,
        capture_output=True,
        text=True,
        timeout=120,
        env=BUILD_ENV,
    )
    local = subprocess.run(
        [
            GO, "list", "-e", "-deps",
            "-f",
            "{{if .Module}}{{if .Module.Main}}{{.ImportPath}}|"
            "{{range .Imports}}{{.}} {{end}}{{end}}{{end}}",
            "./...",
        ],
        **common,
    )
    transitive = subprocess.run(
        [GO, "list", "-e", "-deps", "-f", "{{.ImportPath}}", "./..."],
        **common,
    )
    if local.returncode != 0 or transitive.returncode != 0:
        return None, None
    packages: dict[str, set[str]] = {}
    for line in local.stdout.splitlines():
        if "|" not in line:
            continue
        path, imports = line.split("|", 1)
        packages[path] = set(imports.split())
    return packages, set(transitive.stdout.split())


def _banned_path(path: str) -> bool:
    return path in BANNED_DEP_IMPORTS or path.startswith(BANNED_IMPORT_PREFIXES)


def audit(workspace: Path) -> list[str]:
    """Return every structural rule violation found in the submission."""
    problems: list[str] = []
    if not workspace.is_dir():
        return ["workspace is missing"]
    if not (workspace / "go.mod").is_file():
        problems.append("missing go.mod")

    for dirpath, dirnames, filenames in os.walk(workspace, followlinks=False):
        dirnames[:] = [name for name in dirnames if name not in SKIP_DIRS]
        if "vendor" in dirnames:
            problems.append("vendor/ directory is not allowed")
        for name in list(dirnames):
            if (Path(dirpath) / name).is_symlink():
                problems.append(f"symlinked directory is not allowed: {Path(dirpath) / name}")
                dirnames.remove(name)
        for name in filenames:
            path = Path(dirpath) / name
            if path.is_symlink():
                problems.append(f"symlink is not allowed: {path}")
                continue
            if not path.is_file():
                continue
            if path.suffix.lower() in BANNED_SUFFIXES or name.lower() in BANNED_SUFFIXES:
                problems.append(f"banned file type: {path}")
                continue
            if name in {"go.work", "go.work.sum"}:
                problems.append(f"go workspace file is not allowed: {path}")
                continue
            if path.stat().st_size > 64 * 1024 * 1024:
                problems.append(f"file is too large to audit: {path}")
                continue
            data = path.read_bytes()
            for marker in RUNTIME_MARKERS:
                if marker in data:
                    problems.append(f"runtime marker in {path}")
                    break

    for path in workspace.rglob("*.go"):
        if path.is_symlink():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if BANNED_IMPORT.search(text):
            problems.append(f"banned import in {path}")
        for token in BANNED_TOKEN:
            if token in text:
                problems.append(f"banned construct {token!r} in {path}")

    go_mod = workspace / "go.mod"
    if go_mod.is_file():
        if GO_MOD_DIRECTIVE.search(go_mod.read_text(encoding="utf-8", errors="replace")):
            problems.append("go.mod may not use require, replace or toolchain")
        direct, transitive = _go_imports(workspace)
        if direct is None:
            problems.append("go list could not resolve the module imports")
        else:
            for package, imports in sorted(direct.items()):
                for path in sorted(imports):
                    if path in BANNED_DIRECT_IMPORTS or _banned_path(path):
                        problems.append(f"banned import in {package}: {path}")
            for path in sorted(transitive):
                if _banned_path(path):
                    problems.append(f"banned dependency: {path}")
    return list(dict.fromkeys(problems))


def _lines(data: bytes) -> list[bytes]:
    lines = data.split(b"\n")
    if lines and lines[-1] == b"":
        lines.pop()
    return lines


def _accuracy(stdout: bytes, expected: bytes) -> float:
    exp = _lines(expected)
    got = _lines(stdout)
    if not exp:
        return 0.0
    hits = sum(1 for index, line in enumerate(exp) if index < len(got) and got[index] == line)
    return hits / len(exp)


def exam(workspace: Path, bin_path: Path):
    """Audit, build and run the submission on the hidden exam.

    Returns (stdout, inputs, expected, accuracy) or None when anything is
    wrong. Every criterion goes through this function, so a structural
    violation fails all of them at once.
    """
    if audit(workspace):
        return None
    build = subprocess.run(
        [GO, "build", "-o", str(bin_path), "."],
        cwd=workspace,
        capture_output=True,
        text=True,
        timeout=180,
        env=BUILD_ENV,
    )
    if build.returncode != 0 or not bin_path.is_file():
        return None
    os.chmod(bin_path, 0o755)
    try:
        # A Go binary that still carries an interpreter is not a Go port.
        blob = bin_path.read_bytes()
        if any(marker in blob for marker in RUNTIME_MARKERS):
            return None
        inputs = (DATA / "inputs.txt").read_bytes()
        expected = (DATA / "answers.txt").read_bytes()
        pw = pwd.getpwnam("runner")
        env = dict(RUN_ENV, HOME=pw.pw_dir)
        run = subprocess.run(
            [str(bin_path)],
            cwd="/tmp",
            user=pw.pw_uid,
            group=pw.pw_gid,
            input=inputs,
            capture_output=True,
            timeout=300,
            env=env,
        )
    except Exception:
        return None
    finally:
        bin_path.unlink(missing_ok=True)
    if run.returncode != 0:
        return None
    return run.stdout, inputs, expected, _accuracy(run.stdout, expected)

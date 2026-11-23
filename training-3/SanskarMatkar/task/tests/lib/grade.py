"""Shared grading logic for the three checks (Day 5 hardening).

Lives in /tests/lib (not /tests/checks) so Reward Kit never mistakes it for a
check. Each check calls grade(workspace) and reads the part it scores.

What changed since Day 4, and which attack each part closes:

* The agent's program runs in an EMPTY chroot as user nobody, with an empty
  environment. Inside the jail there is no /tests, no Python, no shell, no
  other file at all - only the static binary itself.
      closes Sugandh cheat 1 (read /tests/data/hidden_expected.txt)
      closes Sugandh cheat 2 (exec the verifier's Python 3.12)
* The Go code may not import packages that start or reach other programs
  (os/exec, syscall, unsafe, plugin, cgo, net...). Breaking this rule scores 0
  on every check.                                   also closes cheat 2
* "No Python" also means no Python SOURCE kept under another name (e.g. the
  original __init__.py renamed to .txt and //go:embed-ed).  also closes cheat 2
* build and no_python only pay when behaviour >= GATE, so a do-nothing program
  that builds and deletes the .py files earns nothing.  closes cheat 3
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / "data"      # /tests/data
GATE = 0.5          # behaviour needed before build / no_python pay anything
NOBODY = 65534
RUN_TIMEOUT = 120   # seconds for the whole 100,000-line run
BUILD_TIMEOUT = 240

# Direct imports that let a program start or talk to anything outside itself.
FORBIDDEN_IMPORTS = {
    "C", "os/exec", "syscall", "unsafe", "plugin", "runtime/cgo", "net",
    "net/http", "net/rpc", "os/signal", "debug/elf", "golang.org/x/sys/unix",
}
PY_SUFFIXES = {".py", ".pyc", ".pyo", ".pyw", ".pyx", ".pyi"}
# Lines only Python source of this library (or any Python script) would have.
PY_MARKERS = re.compile(
    rb"^\s*def\s+titlecase\s*\(|REGEX_AVAILABLE|^\s*import\s+regex\b|"
    rb"^#!\s*/\S*python|^\s*from\s+titlecase\s+import|sys\.modules\[",
    re.MULTILINE,
)

GO_ENV = {
    "PATH": "/usr/local/go/bin:/usr/local/bin:/usr/bin:/bin",
    "HOME": "/tmp",
    "GOCACHE": "/tmp/go-build-cache",
    "GOPATH": "/tmp/gopath",
    "GOTOOLCHAIN": "local",
    "GOPROXY": "off",
    "GOFLAGS": "-mod=readonly",
    "CGO_ENABLED": "0",
}


def _lines(raw: bytes) -> list[bytes]:
    parts = raw.split(b"\n")
    if parts and parts[-1] == b"":
        parts.pop()
    return parts


def _go(args: list[str], cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(["go", *args], cwd=cwd, capture_output=True, text=True,
                          timeout=BUILD_TIMEOUT, env=GO_ENV)


def python_leftovers(workspace: Path) -> list[str]:
    """Files that are Python by name or by content."""
    found = []
    for p in workspace.rglob("*"):
        if p.suffix.lower() in PY_SUFFIXES:
            found.append(str(p))
        elif p.is_file() and not p.is_symlink():
            try:
                if p.stat().st_size <= 8 * 1024 * 1024 and PY_MARKERS.search(p.read_bytes()):
                    found.append(str(p) + " (Python source under another name)")
            except OSError:
                pass
    return found


def bad_imports(repo: Path) -> list[str]:
    """Forbidden or non-standard imports of the agent's own packages."""
    r = _go(["list", "-e", "-f", "{{.ImportPath}}: {{join .Imports \" \"}} {{if .CgoFiles}}C{{end}}",
             "./..."], repo)
    bad = []
    for line in r.stdout.splitlines():
        pkg, _, imps = line.partition(":")
        for imp in imps.split():
            first = imp.split("/")[0]
            third_party = "." in first and not imp.startswith(pkg.split("/")[0])
            if imp in FORBIDDEN_IMPORTS or third_party:
                bad.append(f"{pkg.strip()} imports {imp}")
    return bad


def _jail_preexec(jail: str):
    def setup() -> None:
        os.chroot(jail)
        os.chdir("/")
        os.setgroups([])
        os.setgid(NOBODY)
        os.setuid(NOBODY)
    return setup


def run_in_jail(exe: Path, stdin: bytes) -> bytes:
    """Run the static binary in an empty chroot as nobody. Fails closed."""
    if os.geteuid() != 0:
        raise RuntimeError("verifier must run as root to build the sandbox")
    jail = tempfile.mkdtemp(prefix="jail-")
    try:
        os.chmod(jail, 0o755)
        inside = Path(jail) / "titlecase"
        shutil.copy2(exe, inside)
        os.chmod(inside, 0o555)
        try:
            # "/titlecase" is resolved AFTER preexec_fn has entered the jail.
            r = subprocess.run(["/titlecase"], input=stdin,
                               capture_output=True, timeout=RUN_TIMEOUT, env={},
                               cwd="/", preexec_fn=_jail_preexec(jail))
            return r.stdout
        except subprocess.TimeoutExpired as e:
            print("program timed out")
            return e.stdout or b""
    finally:
        shutil.rmtree(jail, ignore_errors=True)


def grade(workspace: Path) -> dict:
    """Build, inspect and run the agent's program once; return every sub-result."""
    out = {"built": False, "imports_ok": False, "no_python": False, "behaviour": 0.0}
    leftovers = python_leftovers(workspace)
    out["no_python"] = not leftovers
    if leftovers:
        print("Python left:", *leftovers[:20], sep="\n  ")
    if not (workspace / "go.mod").is_file():
        print("no go.mod")
        return out

    inputs = (DATA / "inputs.txt").read_bytes()
    expected = _lines((DATA / "answers.txt").read_bytes())
    if not expected:
        raise RuntimeError("answers.txt is empty - broken task")

    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp) / "repo"
        shutil.copytree(workspace, repo, symlinks=True)
        try:
            out["built"] = _go(["build", "-o", tmp + "/all/", "./..."], repo).returncode == 0
            bad = bad_imports(repo)
            out["imports_ok"] = not bad
            if bad:
                print("forbidden imports:", *bad, sep="\n  ")
            exe = Path(tmp) / "titlecase"
            b = _go(["build", "-trimpath", "-o", str(exe), "."], repo)
        except subprocess.TimeoutExpired:
            print("build timed out")
            return out
        if not out["built"] or b.returncode != 0 or not exe.exists():
            print("build failed:\n" + b.stderr[-2000:])
            return out
        if not out["imports_ok"]:
            return out
        got = _lines(run_in_jail(exe, inputs))

    ok = sum(1 for i, want in enumerate(expected) if i < len(got) and got[i] == want)
    if len(got) != len(expected):
        print(f"line count mismatch: got {len(got)}, expected {len(expected)}")
    print(f"matched {ok}/{len(expected)} hidden lines")
    out["behaviour"] = ok / len(expected)
    return out


def gated(result: dict) -> bool:
    """build and no_python pay only for a program that really titlecases."""
    return result["imports_ok"] and result["behaviour"] >= GATE

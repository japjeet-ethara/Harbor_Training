import json
import re
import subprocess
from pathlib import Path

REPO = Path("/workspace/repo")
DATA = Path("/tests/data")
BIN_PATH = Path("/tmp/titlecase_bin")
OUT_JSON = Path("/logs/verifier/reward.json")

FORBIDDEN_IMPORTS = {"os/exec", "plugin", "syscall", "unsafe", "C"}
FORBIDDEN_CALL_PATTERNS = [
    re.compile(r"\bos\.StartProcess\b"),
    re.compile(r"\bexec\.Command(?:Context)?\b"),
    re.compile(r"\bsyscall\.(?:Exec|ForkExec|StartProcess|Syscall|RawSyscall)\b"),
]


def check_go_mod() -> bool:
    gomod = REPO / "go.mod"
    if not gomod.is_file():
        return False
    for raw in gomod.read_text(encoding="utf-8", errors="replace").split("\n"):
        line = raw.strip()
        if line.startswith(("require ", "require(", "replace ", "replace(")):
            return False
    return True


def check_ast_and_imports() -> bool:
    if not check_go_mod():
        return False
    res = subprocess.run(
        ["go", "list", "-json", "./..."],
        cwd=REPO,
        capture_output=True,
        text=True,
        timeout=30,
    )
    if res.returncode != 0 or not res.stdout.strip():
        return False

    decoder = json.JSONDecoder()
    idx = 0
    text = res.stdout
    while idx < len(text):
        while idx < len(text) and text[idx].isspace():
            idx += 1
        if idx >= len(text):
            break
        pkg, idx = decoder.raw_decode(text, idx)
        if pkg.get("CgoFiles"):
            return False
        for imp in pkg.get("Imports", []):
            if imp in FORBIDDEN_IMPORTS:
                return False

    for go_file in REPO.rglob("*.go"):
        src = go_file.read_text(encoding="utf-8", errors="replace")
        for pat in FORBIDDEN_CALL_PATTERNS:
            if pat.search(src):
                return False
    return True


def check_no_python_assets() -> bool:
    if not REPO.exists():
        return False
    if list(REPO.rglob("*.py")) or list(REPO.rglob("*.pyc")):
        return False
    for f in REPO.rglob("*"):
        if f.is_file() and f.suffix != ".go":
            head = f.read_bytes()[:4096]
            if b"def titlecase(" in head or b"SMALL_WORDS" in head:
                return False
    return True


def build_ok() -> bool:
    if not REPO.exists():
        return False
    r1 = subprocess.run(["go", "build", "./..."], cwd=REPO, capture_output=True, timeout=60)
    if r1.returncode != 0:
        return False
    r2 = subprocess.run(["go", "build", "-o", str(BIN_PATH), "."], cwd=REPO, capture_output=True, timeout=60)
    return r2.returncode == 0


def main() -> None:
    b_raw = build_ok()
    np_raw = b_raw and check_no_python_assets() and check_ast_and_imports()

    beh = 0.0
    if np_raw:
        inp = (DATA / "hidden_inputs.txt").read_text(encoding="utf-8")
        exp = (DATA / "hidden_expected.txt").read_text(encoding="utf-8").split("\n")[:-1]
        run = subprocess.run([str(BIN_PATH)], input=inp, capture_output=True, text=True, encoding="utf-8", timeout=60)
        if run.returncode == 0 and exp:
            out = run.stdout.split("\n")[:-1]
            if len(out) == len(exp):
                raw = sum(1 for e, a in zip(exp, out) if e == a) / len(exp)
                beh = raw if raw >= 0.90 else 0.0

    # Gate build and no_python on minimum behavioral accuracy (>= 0.95)
    b = 1.0 if (b_raw and beh >= 0.95) else 0.0
    np = 1.0 if (np_raw and beh >= 0.95) else 0.0
    reward = 0.0 if np == 0.0 else (b + np + beh * 4.0) / 6.0

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps({
        "build": b,
        "no_python": np,
        "behaviour": beh,
        "reward": reward,
    }, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

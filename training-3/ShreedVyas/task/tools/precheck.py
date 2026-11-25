#!/usr/bin/env python3
"""Pre-submit audit for the titlecase-go Harbor task.
Usage:  python tools/precheck.py <path-to-task-folder>
Every check comes from a point reviewers marked down in earlier submissions.
It READS files only - it never edits anything.
"""
import re, sys
from pathlib import Path

try:
    import tomllib
except ImportError:  # Python < 3.11
    tomllib = None

root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
results = []


def ok(m): results.append(("PASS", m))
def bad(m): results.append(("FAIL", m))
def warn(m): results.append(("WARN", m))


def read(p):
    try:
        return (root / p).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None


def lines(p):
    t = read(p)
    return None if t is None else t.split("\n")[:-1] if t.endswith("\n") else t.split("\n")


# ---------------------------------------------------------------- required files
required = ["task.toml", "instruction.md", "NOTES.md", "README.md",
            "environment/Dockerfile", "solution/solve.sh", "cheat/solve.sh",
            "tests/test.sh", "tests/gen.py",
            "tests/data/inputs.txt", "tests/data/expected.txt",
            "tests/data/hidden_inputs.txt", "tests/data/hidden_expected.txt"]
for f in required:
    (ok if (root / f).is_file() else bad)(f"required file {'present' if (root / f).is_file() else 'MISSING'}: {f}")

# ---------------------------------------------------------------- clutter
junk_names = re.compile(r"(\.bak|\.orig|\.real|~|\.swp|\.exe|\.pyc|\.DS_Store)$|^(Thumbs\.db)$")
for p in root.rglob("*"):
    rel = p.relative_to(root)
    parts = rel.parts
    if ".git" in parts:
        continue
    if p.is_dir() and parts[-1] in ("jobs", "__pycache__", ".pytest_cache", "node_modules"):
        bad(f"clutter directory (delete before submitting): {rel}")
    elif p.is_file():
        if "jobs" in parts or "__pycache__" in parts:
            continue
        if junk_names.search(p.name):
            bad(f"junk/backup file: {rel}")
        try:
            head = p.open("rb").read(4)
            if head.startswith(b"\x7fELF") or head.startswith(b"MZ"):
                bad(f"compiled binary committed: {rel}")
        except OSError:
            pass
        if p.suffix == ".py" and parts[0] not in ("tests", "tools") and "python-titlecase" not in parts:
            warn(f".py file outside tests/: {rel}")

# ---------------------------------------------------------------- NOTES.md
notes = read("NOTES.md") or ""
(ok if re.search(r"github\.com/ppannuto/python-titlecase", notes) else bad)("NOTES.md: repo URL")
(ok if re.search(r"\b[0-9a-f]{40}\b", notes) else bad)("NOTES.md: full 40-char commit SHA")
(ok if re.search(r"\b\d{4}-\d{2}-\d{2}", notes) else bad)("NOTES.md: commit date (from git log %cI)")
(ok if re.search(r"\b(MIT|BSD|Apache)\b", notes) else bad)("NOTES.md: licence name (MIT/BSD/Apache)")
rules = [l for l in notes.splitlines() if re.match(r"\s*\d+[.)]\s+\S", l)]
(ok if len(rules) >= 8 else bad)(f"NOTES.md: numbered rules found = {len(rules)} (need 8+)")
(ok if re.search(r"\bregex\b", notes, re.I) else warn)("NOTES.md: says whether the optional `regex` package was used for the answer key")

# ---------------------------------------------------------------- instruction.md
ins = read("instruction.md") or ""
for label, pat in [("repository description", r"repositor|python-titlecase"), ("what to build", r"stdin"),
                   ("hard rules / standard library", r"standard library"), ("behaviour: byte for byte", r"byte"),
                   ("not checked list", r"not checked"), ("how it is graded", r"graded|grading")]:
    (ok if re.search(pat, ins, re.I) else bad)(f"instruction.md covers: {label}")
for pat in [r"tests/", r"expected\.txt", r"hidden_expected", r"hidden_inputs", r"solve\.sh"]:
    if re.search(pat, ins):
        bad(f"instruction.md leaks/mentions: {pat}")
words = len(ins.split())
(ok if words <= 450 else warn)(f"instruction.md length = {words} words (reviewers marked down long instructions with untested features)")
if re.search(r"clean|well-tested|best practice|readable", ins, re.I):
    warn("instruction.md has vague wording (clean/well-tested/readable) - delete anything you do not test")

# ---------------------------------------------------------------- Dockerfile
df = read("environment/Dockerfile") or ""
froms = re.findall(r"^FROM\s+(\S+)", df, re.M)
(ok if froms and all(":" in f and not f.endswith(":latest") for f in froms) else bad)(f"Dockerfile: pinned FROM tags {froms}")
(ok if re.search(r"^WORKDIR\s+/workspace/repo\s*$", df, re.M) else bad)("Dockerfile: WORKDIR /workspace/repo")
(ok if "titlecase" in df.lower() else bad)("Dockerfile: puts the python-titlecase repo in the image")
if re.search(r"^(COPY|ADD)\b.*\b(solution|tests|expected|hidden|cheat)\b", df, re.M | re.I):
    bad("Dockerfile copies solution/tests/answers/cheat into the agent image (answer leak)")
if re.search(r"\.git\b", df) and not re.search(r"rm\s+-rf?\s+\S*\.git", df):
    warn("Dockerfile mentions .git - make sure .git is NOT copied")

# ---------------------------------------------------------------- task.toml
tt = read("task.toml") or ""
if tomllib and tt:
    try:
        cfg = tomllib.loads(tt)
        ok("task.toml parses as valid TOML")
        name = cfg.get("task", {}).get("name", "")
        (ok if re.fullmatch(r"[a-z0-9][a-z0-9._-]*/[a-z0-9][a-z0-9._-]*", name) else bad)(f"task.toml: [task] name = {name!r} (must look like org/name)")
        an = str(cfg.get("metadata", {}).get("author_name", ""))
        (bad if an.strip().lower() in ("", "your name", "you") else ok)(f"task.toml: author_name = {an!r}")
        em = str(cfg.get("metadata", {}).get("author_email", "x"))
        if "example.com" in em:
            bad("task.toml: placeholder author_email")
        v = cfg.get("verifier", {})
        (ok if v.get("environment_mode") == "separate" else bad)("task.toml: [verifier] environment_mode = 'separate'")
        if "network_mode" in cfg.get("agent", {}):
            ok(f"task.toml: agent network_mode = {cfg['agent']['network_mode']!r}")
        else:
            warn("task.toml: agent network_mode not set")
    except Exception as e:
        bad(f"task.toml does not parse: {e}")
elif not tomllib:
    warn("Python < 3.11: task.toml not parsed (use Python 3.11+ for the full check)")

# ---------------------------------------------------------------- tests
testtxt = "".join((read(p) or "") for p in ["tests/test.sh"]) + "".join(
    (p.read_text(errors="replace") for p in (root / "tests").glob("*") if p.is_file() and p.suffix in (".py", ".toml") and p.name != "gen.py")
)
(ok if "reward.json" in testtxt else bad)("tests: writes reward.json")
(ok if re.search(r"weighted-mean", testtxt) else warn)("tests: weighted-mean aggregation visible")
(ok if re.search(r"weights\s*=|weight\s*=", testtxt) else warn)("tests: explicit weights found - confirm build=1, no_python=1, behaviour=4 (never change them to beat the cheat)")
(ok if "hidden_expected" in testtxt else bad)("tests: behaviour check reads hidden_expected.txt")
if re.search(r"tests/data/(inputs|expected)\.txt", testtxt):
    warn("tests mention the VISIBLE files - behaviour must use only hidden_*")
if re.search(r"\bpytest\b", testtxt) and "rewardkit" not in testtxt.lower():
    warn("tests use plain pytest pass/fail instead of Reward Kit weights")

# ---------------------------------------------------------------- solution / cheat
sol = read("solution/solve.sh") or ""
(ok if re.search(r"\.py", sol) and re.search(r"(rm\b|-delete)", sol) else bad)("solution/solve.sh deletes .py files")
(ok if re.search(r"go\.mod|go mod init", sol) else bad)("solution/solve.sh creates go.mod")
ch = read("cheat/solve.sh") or ""
if re.search(r"(rm\b[^\n]*\.py|-delete|find\b[^\n]*\.py)", ch):
    bad("cheat/solve.sh deletes .py files -> it would score ~0.33 (above the 0.2 bar). Leave the .py files in place")
else:
    ok("cheat/solve.sh leaves .py files (expected cheat reward ~0.17)")
(ok if re.search(r"cheat_answers|expected", ch) else warn)("cheat/solve.sh prints the visible answers")
if sol and sol == ch:
    bad("solution/solve.sh is identical to cheat/solve.sh (oracle must be the real port)")

# ---------------------------------------------------------------- data
d = {n: lines(f"tests/data/{n}.txt") for n in ("inputs", "expected", "hidden_inputs", "hidden_expected")}
if all(v is not None for v in d.values()):
    for a, b in (("inputs", "expected"), ("hidden_inputs", "hidden_expected")):
        (ok if len(d[a]) == len(d[b]) else bad)(f"data: {a}={len(d[a])} lines, {b}={len(d[b])} lines (must match)")
    (ok if len(d["inputs"]) == 2000 and len(d["hidden_inputs"]) == 2000 else bad)("data: 2000 visible + 2000 hidden inputs")
    ov = set(d["inputs"]) & set(d["hidden_inputs"])
    (ok if len(ov) <= 0.02 * 2000 else warn)(f"data: {len(ov)} inputs appear in BOTH visible and hidden (keep this near 0)")
    uniq = len(set(d["hidden_inputs"])) / max(len(d["hidden_inputs"]), 1)
    (ok if uniq >= 0.9 else warn)(f"data: {uniq:.0%} of hidden inputs are unique")
    if d["hidden_inputs"]:
        tricky = sum(1 for l in d["hidden_inputs"] if re.search(r"[0-9_:/@.\-'\"&()]|[A-Z]{2,}|[^\x00-\x7f]", l))
        (ok if tricky >= 0.3 * len(d["hidden_inputs"]) else warn)(f"data: {tricky}/{len(d['hidden_inputs'])} hidden lines contain tricky characters (hidden set must hold the hard cases)")
    if d["expected"] == d["inputs"]:
        bad("data: expected.txt equals inputs.txt - answers were not produced by titlecase()")
gen = read("tests/gen.py") or ""
(ok if re.search(r"random\.seed\(\s*1\s*\)", gen) else bad)("gen.py: random.seed(1)")
(ok if "titlecase" in gen else bad)("gen.py: calls the original titlecase()")

# ---------------------------------------------------------------- hand-in
rd = read("README.md") or ""
m = re.search(r"##\s*Hand-?in\s*\n(.*)", rd, re.S | re.I)
hand = [l for l in (m.group(1).splitlines() if m else []) if l.strip()]
(ok if len(hand) >= 2 else bad)("README.md: '## Hand-in' section with the two lines")
if re.search(r"TODO|FIXME|YOUR NAME|<[A-Za-z _-]+>|lorem", rd):
    bad("README.md has template/placeholder text")
shots = [p for p in (root / "screenshots").glob("*")] if (root / "screenshots").is_dir() else []
names = " ".join(p.name.lower() for p in shots)
for k in ("oracle", "nop", "cheat"):
    (ok if k in names else bad)(f"screenshots/: image for {k} (real screenshot of your own harbor run)")
for ref in re.findall(r"`([\w./-]+\.(?:md|sh|py|toml|png|jpg|txt))`", rd):
    if not (root / ref).exists():
        bad(f"README.md mentions a file that is not there: {ref}")

# ---------------------------------------------------------------- report
w = max(len(r[0]) for r in results)
for lvl, msg in results:
    print(f"[{lvl}] {msg}")
fails = sum(1 for l, _ in results if l == "FAIL")
warns = sum(1 for l, _ in results if l == "WARN")
print(f"\n{len(results)} checks: {fails} FAIL, {warns} WARN")
print("NOTE: this script cannot prove the NOTES.md examples are true or that rewards are real - you must verify those yourself.")
sys.exit(1 if fails else 0)

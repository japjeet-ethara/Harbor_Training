# -*- coding: utf-8 -*-
"""Count dev and hidden lines changed by one minimal mutant per titlecase rule.

Reads the original package, copies it outside the project, and applies each
mutant with a single exact replacement. Does not write under titlecase-go.
"""

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPO = ROOT / "titlecase-go" / "environment" / "repo"
PACKAGE = REPO / "titlecase"
DATA = ROOT / "titlecase-go" / "tests" / "data"


def require(path: Path, directory: bool = False) -> None:
    ok = path.is_dir() if directory else path.is_file()
    if not ok:
        raise SystemExit(f"abort: missing {path}")


RUNNER = r"""
import json
import sys
from pathlib import Path

temp_root = Path(sys.argv[1]).resolve()
dev_in, hidden_in, dev_out, hidden_out = sys.argv[2:6]

import titlecase as titlecase_mod

mod_file = Path(titlecase_mod.__file__).resolve()
if not mod_file.is_relative_to(temp_root):
    raise SystemExit("titlecase loaded from %s, not %s" % (mod_file, temp_root))

fn = titlecase_mod.titlecase


def load(path):
    with open(path, encoding="utf-8", newline="\n") as fh:
        data = fh.read()
    if not data.endswith("\n"):
        raise SystemExit("%s: no final newline" % path)
    return data[:-1].split("\n")


def run(src, dst):
    lines = load(src)
    out = [fn(line) for line in lines]
    with open(dst, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(out, fh, ensure_ascii=False)


run(dev_in, dev_out)
run(hidden_in, hidden_out)
"""

# Each mutant replaces old with new. old must occur exactly once.
MUTANTS = [
    {
        "name": "line-breaks",
        "desc": "keep every line break instead of collapsing consecutive breaks",
        "old": "lines = regex.split('[\\r\\n]+', text)",
        "new": "lines = regex.split('[\\r\\n]', text)",
    },
    {
        "name": "callback",
        "desc": "ignore a callback result and keep running the later rules",
        "old": "if callback:",
        "new": "if False and callback:",
    },
    {
        "name": "all-caps-initials",
        "desc": "do not keep dotted initials unchanged on an all-caps line",
        "old": "if UC_INITIALS.match(word):",
        "new": "if False and UC_INITIALS.match(word):",
    },
    {
        "name": "apostrophe-o",
        "desc": "do not capitalize either side of an O' apostrophe name",
        "old": "word = word[0].upper() + word[1] + word[2].upper() + word[3:]",
        "new": "word = word[0].lower() + word[1] + word[2].lower() + word[3:]",
    },
    {
        "name": "apostrophe-dl",
        "desc": "capitalize a leading d/l and lowercase the letter after the apostrophe",
        "old": "word = word[0].lower() + word[1] + word[2].upper() + word[3:]",
        "new": "word = word[0].upper() + word[1] + word[2].lower() + word[3:]",
    },
    {
        "name": "mc-prefix",
        "desc": "disable the Mc/MC prefix rewrite",
        "old": "MAC_MC.match(word)",
        "new": "None",
    },
    {
        "name": "honorific",
        "desc": "disable Mr/Mrs/Ms/Dr initial capitalization",
        "old": "MR_MRS_MS_DR.match(word)",
        "new": "None",
    },
    {
        "name": "inline-period",
        "desc": "do not leave a word with an inline period unchanged",
        "old": "INLINE_PERIOD.search(word) or ",
        "new": "",
    },
    {
        "name": "internal-caps",
        "desc": "do not keep a word that already has a capital after its first character",
        "old": " or (not all_caps and UC_ELSEWHERE.match(word))",
        "new": "",
    },
    {
        "name": "small-word",
        "desc": "do not lowercase a word that is exactly a small word",
        "old": "if SMALL_WORDS.match(word):",
        "new": "if False and SMALL_WORDS.match(word):",
    },
    {
        "name": "slash",
        "desc": "do not title-case each piece of a slash-separated word",
        "old": 'if "/" in word and "//" not in word:',
        "new": 'if False and "/" in word and "//" not in word:',
    },
    {
        "name": "hyphen",
        "desc": "do not title-case each piece of a hyphenated word",
        "old": "if '-' in word:",
        "new": "if False and '-' in word:",
    },
    {
        "name": "all-caps-lower",
        "desc": "do not lowercase remaining words on an all-caps line",
        "old": "word = word.lower()",
        "new": "word = word",
    },
    {
        "name": "consonants",
        "desc": "do not uppercase an all-consonant word as an acronym",
        "old": "if is_all_consonants and len(word) > 2:",
        "new": "if False and is_all_consonants and len(word) > 2:",
    },
    {
        "name": "cap-first",
        "desc": "do not capitalize the first letter of an ordinary word",
        "old": "tc_line.append(CAPFIRST.sub(lambda m: m.group(0).upper(), word))",
        "new": "tc_line.append(word)",
    },
    {
        "name": "leading-nonletter",
        "desc": "capitalize the first letter of a token that starts with a digit",
        "old": 'CAPFIRST = regex.compile(r"^[%s]*?([\\w])" % PUNCT)',
        "new": 'CAPFIRST = regex.compile(r"^[%s0-9]*([A-Za-z])" % PUNCT)',
    },
    {
        "name": "small-first",
        "desc": "do not capitalize a small word at the start of the line",
        "old": (
            "tc_line[0] = SMALL_FIRST.sub(lambda m: '%s%s' % (\n"
            "                    m.group(1),\n"
            "                    m.group(2).capitalize()\n"
            "                ), tc_line[0])"
        ),
        "new": "tc_line[0] = tc_line[0]",
    },
    {
        "name": "small-last",
        "desc": "do not capitalize a small word at the end of the line",
        "old": "m.group(0).capitalize()",
        "new": "m.group(0)",
    },
    {
        "name": "spaces",
        "desc": "join words with a single ordinary space",
        "old": "if normalise_space_characters:",
        "new": "if not normalise_space_characters:",
    },
    {
        "name": "subphrase",
        "desc": "do not capitalize a small word that opens a subphrase",
        "old": (
            "result = SUBPHRASE.sub(lambda m: '%s%s' % (\n"
            "            m.group(1),\n"
            "            m.group(2).capitalize()\n"
            "        ), result)"
        ),
        "new": "result = result",
    },
    {
        "name": "drop-vs-dot",
        "desc": "remove vs. from the small-word list, keeping vs",
        "old": "vs\\.?",
        "new": "vs",
    },
    {
        "name": "drop-via",
        "desc": "remove via from the small-word list",
        "old": "|via",
        "new": "",
    },
    {
        "name": "blank-text",
        "desc": "return a single space when the whole input is empty or whitespace",
        "old": "    if preserve_blank_lines:",
        "new": '    if small_first_last and text.strip() == "":\n        return " "\n    if preserve_blank_lines:',
    },
]


def load_lines(path):
    with open(path, encoding="utf-8", newline="\n") as fh:
        data = fh.read()
    if not data.endswith("\n"):
        raise SystemExit("%s: no final newline" % path)
    return data[:-1].split("\n")


def tree_sha256(root):
    digest = hashlib.sha256()
    files = sorted(
        (p for p in root.rglob("*") if p.is_file()),
        key=lambda p: p.relative_to(root).as_posix(),
    )
    for path in files:
        rel = path.relative_to(root).as_posix()
        digest.update(rel.encode("utf-8"))
        digest.update(b"\0")
        with open(path, "rb") as fh:
            digest.update(fh.read())
        digest.update(b"\0")
    return digest.hexdigest()


def apply_once(text, old, new, name):
    count = text.count(old)
    if count != 1:
        raise SystemExit("%s: snippet occurs %d times, expected 1" % (name, count))
    return text.replace(old, new, 1)


def run_copy(source_text, dev_path, hidden_path):
    temp_root = Path(tempfile.mkdtemp(prefix="titlecase-mutant-"))
    try:
        dest = temp_root / "titlecase"
        shutil.copytree(PACKAGE, dest)
        pyc = dest / "__pycache__"
        if pyc.exists():
            shutil.rmtree(pyc)
        init_path = dest / "__init__.py"
        with open(init_path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(source_text)
        dev_out = temp_root / "dev_out.json"
        hidden_out = temp_root / "hidden_out.json"
        runner = temp_root / "run_mutant.py"
        with open(runner, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(RUNNER)
        env = os.environ.copy()
        env["PYTHONPATH"] = str(temp_root)
        env["PYTHONIOENCODING"] = "utf-8"
        proc = subprocess.run(
            [
                sys.executable,
                str(runner),
                str(temp_root),
                str(dev_path),
                str(hidden_path),
                str(dev_out),
                str(hidden_out),
            ],
            cwd=str(temp_root),
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=180,
        )
        if proc.returncode != 0:
            detail = (proc.stderr or proc.stdout or "no output").strip().splitlines()
            reason = detail[-1] if detail else "exit %d" % proc.returncode
            return None, reason
        with open(dev_out, encoding="utf-8", newline="\n") as fh:
            dev_actual = json.load(fh)
        with open(hidden_out, encoding="utf-8", newline="\n") as fh:
            hidden_actual = json.load(fh)
        return (dev_actual, hidden_actual), None
    except subprocess.TimeoutExpired:
        return None, "timeout"
    except (OSError, json.JSONDecodeError) as exc:
        return None, "%s: %s" % (type(exc).__name__, exc)
    finally:
        shutil.rmtree(temp_root, ignore_errors=True)


def count_changed(actual, expected, sources, keep_examples):
    if len(actual) != len(expected) or len(actual) != len(sources):
        return None, []
    changed = 0
    examples = []
    for got, want, src in zip(actual, expected, sources):
        if got != want:
            changed += 1
            if keep_examples and len(examples) < 3:
                examples.append(src)
    return changed, examples


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
    require(REPO, directory=True)
    require(PACKAGE, directory=True)
    require(DATA, directory=True)
    require(PACKAGE / "__init__.py")
    require(DATA / "inputs.txt")
    require(DATA / "expected.txt")
    require(DATA / "hidden_inputs.txt")
    require(DATA / "hidden_expected.txt")
    before = tree_sha256(REPO)
    with open(PACKAGE / "__init__.py", encoding="utf-8", newline="\n") as fh:
        original = fh.read()

    for spec in MUTANTS:
        apply_once(original, spec["old"], spec["new"], spec["name"])

    dev_in = load_lines(DATA / "inputs.txt")
    dev_expected = load_lines(DATA / "expected.txt")
    hidden_in = load_lines(DATA / "hidden_inputs.txt")
    hidden_expected = load_lines(DATA / "hidden_expected.txt")

    print("baseline", file=sys.stderr)
    baseline, err = run_copy(original, DATA / "inputs.txt", DATA / "hidden_inputs.txt")
    if err or baseline is None:
        raise SystemExit("unmodified titlecase failed: %s" % err)
    base_dev, _ = count_changed(baseline[0], dev_expected, dev_in, False)
    base_hidden, _ = count_changed(baseline[1], hidden_expected, hidden_in, False)
    if base_dev != 0 or base_hidden != 0:
        raise SystemExit(
            "unmodified titlecase disagrees with expected files: dev=%s hidden=%s"
            % (base_dev, base_hidden)
        )

    results = []
    for number, spec in enumerate(MUTANTS, start=1):
        print("mutant %d %s" % (number, spec["name"]), file=sys.stderr)
        mutated = apply_once(original, spec["old"], spec["new"], spec["name"])
        actual, err = run_copy(mutated, DATA / "inputs.txt", DATA / "hidden_inputs.txt")
        row = {
            "number": number,
            "name": spec["name"],
            "desc": spec["desc"],
            "crash": err,
            "dev": None,
            "hidden": None,
            "examples": [],
        }
        if err is None:
            dev_n, _ = count_changed(actual[0], dev_expected, dev_in, False)
            hidden_n, examples = count_changed(
                actual[1], hidden_expected, hidden_in, True
            )
            if dev_n is None or hidden_n is None:
                row["crash"] = "output line count does not match the input files"
            else:
                row["dev"] = dev_n
                row["hidden"] = hidden_n
                row["examples"] = examples
        results.append(row)

    after = tree_sha256(REPO)

    print(
        "%-4s  %-18s  %8s  %8s  %-6s  %s"
        % ("#", "rule", "dev", "hidden", "status", "change")
    )
    for row in results:
        status = "CRASH" if row["crash"] else ""
        dev = "-" if row["dev"] is None else str(row["dev"])
        hidden = "-" if row["hidden"] is None else str(row["hidden"])
        print(
            "%-4d  %-18s  %8s  %8s  %-6s  %s"
            % (row["number"], row["name"], dev, hidden, status, row["desc"])
        )
        if row["crash"]:
            print("      %s" % row["crash"])

    print()
    print("Mutants with fewer than 10 hidden lines changed:")
    sparse = [
        row
        for row in results
        if row["crash"] is None and row["hidden"] is not None and row["hidden"] < 10
    ]
    if not sparse:
        print("none")
    for row in sparse:
        print(
            "[%d] %s  hidden=%d  %s"
            % (row["number"], row["name"], row["hidden"], row["desc"])
        )
        if not row["examples"]:
            print("  none")
        for example in row["examples"]:
            print("  %s" % repr(example))

    print()
    print("repo sha256 before: %s" % before)
    print("repo sha256 after:  %s" % after)
    assert before == after, "titlecase-go/environment/repo changed"
    print("repo unchanged: True")


if __name__ == "__main__":
    main()

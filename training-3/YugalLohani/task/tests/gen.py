#!/usr/bin/env python3
"""Generate the frozen inputs and answers for the titlecase-go task.

Runs on the task author's machine, NOT inside Docker, with the reference
interpreter: CPython 3.12 and regex==2024.11.6, e.g.

    uv venv --python 3.12 .venv-titlecase
    uv pip install --python .venv-titlecase/bin/python 'regex==2024.11.6'
    .venv-titlecase/bin/python tests/gen.py

It needs the python-titlecase checkout (commit
42f43e2de55bf003b286c6f8e8d8b2d26676a167) beside the task folder or in one of
its parent folders, or at the path given by TITLECASE_DIR.

Every expected line comes from running the ORIGINAL titlecase(); nothing is
written by hand.
"""

from __future__ import annotations

import collections
import os
import random
import sys
import unicodedata
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
EXPECTED_SHA = "42f43e2de55bf003b286c6f8e8d8b2d26676a167"
N_VISIBLE = 2000
N_HIDDEN = 2000


def find_checkout() -> Path:
    if os.environ.get("TITLECASE_DIR"):
        return Path(os.environ["TITLECASE_DIR"]).resolve()
    for parent in HERE.parents[1:]:
        candidate = parent / "python-titlecase"
        if (candidate / "titlecase" / "__init__.py").is_file():
            return candidate
    sys.exit("python-titlecase checkout not found (set TITLECASE_DIR)")


def check_reference(root: Path):
    if (root / ".git").exists():
        import subprocess

        sha = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"],
                             capture_output=True, text=True).stdout.strip()
        if sha != EXPECTED_SHA:
            sys.exit(f"{root} is at {sha!r}, expected {EXPECTED_SHA}")
    if sys.version_info[:2] != (3, 12) or unicodedata.unidata_version != "15.0.0":
        sys.exit(f"need CPython 3.12 (Unicode 15.0.0), got {sys.version.split()[0]}")
    import regex

    if regex.__version__ != "2.5.148":  # regex==2024.11.6
        sys.exit(f"need regex==2024.11.6 (module version 2.5.148), got {regex.__version__}")
    sys.path.insert(0, str(root))
    import titlecase

    if not titlecase.REGEX_AVAILABLE or titlecase.__version__ != "2.4.1":
        sys.exit("titlecase did not load the regex code path of version 2.4.1")
    return titlecase.titlecase


# ---------------------------------------------------------------- word pools

NORMAL = """lord rings wind willows tale two cities man plan canal world story hope
new war peace quick brown fox jumps lazy dog river city night day summer winter
history science guide beginner python go golang program language data model learning
deep network machine engine house garden kitchen music life love time road home book
star wars empire strikes back return king queen prince little women old sea great
gatsby catcher rye pride prejudice sense sensibility brave grapes wrath harry potter
stone chamber secrets prisoner fire goblet order phoenix blood mystery murder orient
express hound baskervilles hunger games catching last mile green mile one hundred years
solitude art motorcycle maintenance zen hitchhiker galaxy""".split()

SMALL = "a an and as at but by en for if in of on or the to v v. via vs vs.".split()
SMALL_CASED = SMALL + ["A", "The", "THE", "Of", "OF", "And", "AND", "In", "To", "Vs.", "V."]

TRICKY_WORDS = """iPhone eBay iPad LaTeX McDonald's macOS YouTube GitHub JavaScript
example.com www.example.org e.g. i.e. U.S.A. U.K. A.B. A.B.C. U.S. v2.0 3.14 1.5x
html css xml pdf nth st mr mrs ms dr Mr. Dr. MRS. rhythm crypt sky myth gym
mcdonald mcgregor MCGREGOR mcx mc MC macdonald mccartney Mcintosh mc-donald
d'artagnan o'neil l'oreal o'brien d'angelo l'amour O'REILLY d‘arcy o‘neil d’angelo o’neil
either/or and/or input/output TCP/IP http//x a/b/c 1/2
step-by-step out-of-the-box state-of-the-art self-aware x-ray e-mail MAN-MADE a-b
"hello" (world) [note] {braces} 'single' “curly” ‘single’ ’tis ”quote” «guillemets»
-dash- --double --- ... !wow ?why @user #hashtag $5 50% &more *star* _under_ `tick`
2nd 3d 21st 1990s 100 2024 0
https://github.com/ppannuto/python-titlecase mailto:a@b.c user@example.com""".split()

UNICODE_WORDS = """straße ßeas ﬁsh ﬂower ŉ ǆungla ǅungla ǄUNGLA élan ÉLAN Ñandú niño café
façade naïve Øresund æon ÆON œuvre İstanbul ıs İn ſo ſmall ſtate ﬀ ﬃx
ΟΔΟΣ ΣΟΦΟΣ οδος σοφος Σ ΣΑΣ ΑΘΗΝΑ Ελλάδα λόγος ΛΌΓΟΣ ΜΥΘΟΣ
Москва ПРИВЕТ мир Ёлка
日本 東京 中文 한국어 🎉 🚀 ✓ ★""".split() + ["\u212aing", "\u212a", "co\u0301te", "e\u0301"]

SPACES = [" "] * 30 + ["  ", "\t", "\u00a0", "\u2003", "\u2009", "\u3000", "\u202f", "\x85", "\u2028", "   "]
SUBPHRASE_PUNCT = [":", ".", ";", "?", "!", "-", "–", "‒", "—", "―"]

SENTENCES = [
    "the lord of the rings", "a tale of two cities", "the wind in the willows",
    "star wars: a new hope", "harry potter and the chamber of secrets",
    "zen and the art of motorcycle maintenance", "the hitchhiker's guide to the galaxy",
    "one hundred years of solitude", "of mice and men", "what is it for?",
    "the old man and the sea", "a man, a plan, a canal: panama",
    "murder on the orient express", "the hound of the baskervilles",
    "where are you going, where have you been?", "and then there were none",
    "to kill a mockingbird", "the catcher in the rye", "pride and prejudice",
    "learning python: a beginner's guide", "q&a: how to win friends",
    "the iphone vs. the ebay app", "apple v. orange", "notes on html and css",
    "the u.s.a. and the u.k.", "mcdonald's and o'neil's pub", "dr. no and mr. smith",
]


def recase(s: str) -> str:
    k = random.random()
    if k < 0.45:
        return s.lower()
    if k < 0.65:
        return s.upper()
    if k < 0.73:
        return s.title()
    if k < 0.83:
        return "".join(c.upper() if random.random() < 0.4 else c.lower() for c in s)
    return s


def pick_word() -> str:
    k = random.random()
    if k < 0.40:
        return random.choice(NORMAL)
    if k < 0.62:
        return random.choice(SMALL_CASED)
    if k < 0.85:
        return random.choice(TRICKY_WORDS)
    return random.choice(UNICODE_WORDS)


def make_line() -> str:
    k = random.random()
    if k < 0.30:
        words = [pick_word() for _ in range(random.randint(1, 8))]
        line = random.choice(SPACES).join(words) if random.random() < 0.2 else " ".join(words)
        line = recase(line) if random.random() < 0.6 else line
    elif k < 0.48:
        line = recase(random.choice(SENTENCES))
        if random.random() < 0.3:
            line = line + " " + random.choice(SMALL_CASED)
    elif k < 0.62:  # subphrases
        a = " ".join(pick_word() for _ in range(random.randint(1, 3)))
        b = " ".join([random.choice(SMALL_CASED)] + [pick_word() for _ in range(random.randint(0, 3))])
        sep = random.choice(SUBPHRASE_PUNCT) + random.choice([" ", " ", " ", "\u00a0", "  "])
        if random.random() < 0.3:
            sep = " " + sep
        line = recase(a + sep + b)
    elif k < 0.74:  # many small words, first/last positions, punctuation around
        words = [random.choice(SMALL_CASED + NORMAL) for _ in range(random.randint(1, 6))]
        if random.random() < 0.5:
            words[0] = random.choice(["(", '"', "“", "‘", "'", "[", "...", "¿", "’"]) + words[0]
        if random.random() < 0.5:
            words[-1] = words[-1] + random.choice(["?", "!", ".", ")", '"', "?!", ".)", "…", ":", "”"])
        line = recase(" ".join(words))
    elif k < 0.84:  # unicode-heavy
        words = [random.choice(UNICODE_WORDS + SMALL_CASED + NORMAL) for _ in range(random.randint(1, 6))]
        line = random.choice(SPACES).join(words)
        if random.random() < 0.4:
            line = recase(line)
    elif k < 0.92:  # compounds
        parts = [random.choice(SMALL_CASED + NORMAL + UNICODE_WORDS[:12]) for _ in range(random.randint(2, 4))]
        joiner = random.choice(["-", "/", "-", "/", "//"])
        line = " ".join([pick_word(), joiner.join(parts), pick_word()][: random.randint(1, 3)])
        line = recase(line)
    elif k < 0.97:  # whitespace at the edges
        core = " ".join(pick_word() for _ in range(random.randint(1, 4)))
        line = random.choice(SPACES) + core + random.choice(["", " ", "  ", "\t"])
        line = recase(line)
    else:  # degenerate
        line = random.choice(["", " ", "  ", "\t", "123", "123 456", "A", "a", "I", "-", "/", ":", "a:", ": a",
                              "THE", "the", "Of", "...", "ΣΣ", "ß", "ﬁ", "İ"])
    return line


def make_set(n: int, seen: set[str], tc) -> tuple[list[str], list[str]]:
    inputs, outputs = [], []
    while len(inputs) < n:
        line = make_line()
        if line in seen or "\n" in line or "\r" in line:
            continue
        # Keep inputs that titlecase leaves unchanged rare, so an "echo the
        # input" program cannot collect many free points.
        out = tc(line)
        if out == line and random.random() < 0.85:
            continue
        if "\n" in out or "\r" in out:
            continue
        seen.add(line)
        inputs.append(line)
        outputs.append(out)
    return inputs, outputs


def write_lines(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        for line in lines:
            fh.write(line + "\n")


def describe(name: str, inputs: list[str], outputs: list[str]) -> None:
    c = collections.Counter()
    for i, o in zip(inputs, outputs):
        c["unchanged"] += i == o
        c["all_caps"] += i.upper() == i and i != ""
        c["non_ascii"] += any(ord(ch) > 127 for ch in i)
        c["unicode_space"] += any(ch in "\u00a0\u2003\u2009\u3000\u202f\x85\u2028\t" for ch in i)
        c["edge_space"] += i[:1].isspace() or i[-1:].isspace()
        c["hyphen_or_slash"] += "-" in i or "/" in i
        c["subphrase"] += any(p + " " in i for p in SUBPHRASE_PUNCT)
        c["full_case_map"] += any(len(ch.upper()) > 1 or len(ch.lower()) > 1 for ch in i)
        c["sigma"] += "Σ" in i
        c["fold_IsK"] += any(ch in "\u0130\u017f\u212a" for ch in i)
        c["empty"] += i == ""
    print(f"{name}: {len(inputs)} lines; " + ", ".join(f"{k}={v}" for k, v in sorted(c.items())))


def main() -> None:
    tc = check_reference(find_checkout())
    random.seed(1)
    seen: set[str] = set()
    vis_in, vis_out = make_set(N_VISIBLE, seen, tc)
    hid_in, hid_out = make_set(N_HIDDEN, seen, tc)
    write_lines(DATA / "inputs.txt", vis_in)
    write_lines(DATA / "expected.txt", vis_out)
    write_lines(DATA / "hidden_inputs.txt", hid_in)
    write_lines(DATA / "hidden_expected.txt", hid_out)
    describe("visible", vis_in, vis_out)
    describe("hidden", hid_in, hid_out)
    same_index = sum(a == b for a, b in zip(vis_out, hid_out))
    print(f"visible/hidden expected lines equal at the same index: {same_index}")


if __name__ == "__main__":
    main()

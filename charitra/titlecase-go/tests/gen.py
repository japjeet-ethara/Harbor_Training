#!/usr/bin/env python3
"""Rebuild frozen titlecase fixtures from the pinned original, never hand-made answers.

Run from the task root: python3.12 -S tests/gen.py
An alternate unmodified source checkout can be supplied with --source PATH.
Importing this module does not generate files or register verifier criteria.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import platform
import random
import sys
import unicodedata

UPSTREAM_URL = "https://github.com/ppannuto/python-titlecase"
UPSTREAM_SHA = "42f43e2de55bf003b286c6f8e8d8b2d26676a167"
SOURCE_SHA256 = "a3d0b99857c7672b9a13ec9df54aa187082be7d39b202dc0511e67e6f7873ef0"
SEED = 1
COUNT = 2000


def reference_module(source: Path):
    module_path = source / "titlecase" / "__init__.py"
    actual = hashlib.sha256(module_path.read_bytes()).hexdigest()
    if actual != SOURCE_SHA256:
        raise RuntimeError(f"Reference source hash differs from the pinned original: {actual}")
    spec = importlib.util.spec_from_file_location("_pinned_titlecase_reference", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Cannot load the original source")
    module = importlib.util.module_from_spec(spec)
    # Execute the original bytes without generating __pycache__ in the starter snapshot.
    exec(compile(module_path.read_bytes(), str(module_path), "exec"), module.__dict__)
    if module.REGEX_AVAILABLE:
        raise RuntimeError("Optional third-party regex backend was loaded. Run python3.12 -S tests/gen.py")
    return module


def upstream_inputs(source: Path) -> list[str]:
    """Extract only input literals; never import or copy upstream expected answers."""
    tree = ast.parse((source / "titlecase" / "tests.py").read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "TEST_DATA" for t in node.targets):
            values = ast.literal_eval(node.value)
            return [pair[0] for pair in values if isinstance(pair[0], str) and "\n" not in pair[0] and "\r" not in pair[0]]
    raise RuntimeError("Pinned upstream TEST_DATA was not found")


def fixed_inputs(source: Path) -> list[str]:
    cases = upstream_inputs(source) + [
        "", " ", "  ", "\t", "\t \t", "the lord of the rings",
        "the end of", " the end of ", "  the   lord\tof the rings  ",
        "a an and as at but by en for if in of on or the to v v. via vs vs.",
        "A AN AND AS AT BUT BY EN FOR IF IN OF ON OR THE TO V V. VIA VS VS.",
        "NASA", "visit NASA now", "NASA AND THE MOON", "visit iPhone and eBay now",
        "iPhone eBay iOS macOS aBc", "hello A.B. and U.S.A. now", "U.S.A. AND A.B.",
        "a.b", "a..b", "1.2 3rd ¼.½ _._", "foo//bar", "http://example.com/a-title",
        "https://example.com/path-and/more?q=1", "the and/or of/on story", "a-b end-to-end",
        "in/of/by-the-and/a-b", "a--b --- c", "/a//b/", "a/b-c/d-e/f-g",
        "mcdonald mcDonald MCDONALD", "mcx McX MCX mcd McD MCD",
        "mr mrs ms dr MR MRS MS DR mR mRS mS dR", "d'artagnan l'amour o'brien",
        "D'ARTAGNAN L'AMOUR O'BRIEN", "d‘artagnan l‘amour o‘brien", "o'neill's l'amour's",
        "cnn BBC html XML shy dry rhythm nth ng", "ST st TV tv FBI fbi CNN cnn",
        "[the story] {the story} (the story)", "[[the story]] [and] the end]", "\\the path \\and end",
        "'the story' \"a tale\" “an ending” ‘a test’", "¿the story? ¡an ending!",
        "foo: the bar; an ending. and then? or now! but why - the end",
        "foo: andThing; theThing. aBc", "foo — the bar – an ending ‒ a story ― or not",
        "foo:  the bar", "foo:\tthe bar", "---the---", "___the___", "123the 456and 789of",
        "straße STRASSE ß ﬀ ﬃ ﬄ ﬅ ﬆ", "ﬂower Æther œuvre ǳung ǆung ǰolt",
        "ΟΣ ΟΣΑ Σ σ ς", "οσ οσα ος σοσ", "ΟΣ\u0301 ΟΣ\u0301Α", "İSTANBUL IŞIK ıstanbul İstanbul",
        "ſome Kelvin ıi İi", "élève ÉLÈVE déjà-vu", "ábc àBC čaj øresund đuro",
        "Հայերեն ქართული русский УКРАЇНА", "中文 日本語 한글 हिन्दी",
        "a\u0301bc e\u0301clair \u0301the", "ǅURO ǄURO ǆuro ǳung", "ᾀ ᾈ ᾳ ᾼ ῳ ῼ",
        "ⅰ Ⅳ ⅻ ² ³ ¼ ½ ① Ⅷ", "𝔞𝔟 𝔄𝔅 𝕒𝕓 𝔸𝔹", "𐐨𐐩 𐐀𐐁 𐑀𐑁",
        "👩‍💻 the title 👨🏽‍🚀", "😀the story ★the end", "the\u200btitle and\ufeffword",
        "a\x00b the\x00end", "\x07the\x08and\x1bof", "foo\x7fbar baz", "a\u202ebc and\u2066word",
    ]
    # Python re treats these as whitespace; LF/CR are record delimiters and excluded.
    spaces = ["\t", "\v", "\f", "\x1c", "\x1d", "\x1e", "\x1f", "\x85", "\u00a0", "\u1680",
              "\u2000", "\u2001", "\u2002", "\u2003", "\u2004", "\u2005", "\u2006", "\u2007",
              "\u2008", "\u2009", "\u200a", "\u2028", "\u2029", "\u202f", "\u205f", "\u3000"]
    for space in spaces:
        cases.extend([f"the{space}lord{space}of{space}NASA", f"{space}and{space}THE{space}"])
    # These exceed bufio.Scanner's default 64 KiB token limit.
    cases.extend(["the " + "lord of the rings " * 6000 + "end", "a " + "straße and Σ " * 6000 + "finish"])
    return cases


def random_title(rng: random.Random) -> str:
    words = ["the", "a", "an", "and", "as", "at", "but", "by", "en", "for", "if", "in", "of", "on", "or", "to", "via", "vs", "vs.", "v", "v.",
             "river", "harbor", "paper", "title", "world", "science", "orbit", "willow", "bridge", "oak", "saffron", "book", "day", "night", "small", "word", "apple", "zebra",
             "NASA", "CNN", "BBC", "XML", "HTML", "iPhone", "eBay", "macOS", "A.B.", "U.S.A.", "D.J.", "1.2", "3rd", "_word", "123abc", "a.B", "foo.example",
             "mcdonald", "McDonald", "MCDONALD", "mcx", "MCX", "mr", "mrs", "ms", "dr", "DR", "mR", "o'brien", "d'artagnan", "l'amour", "l‘amour",
             "cnn", "rhythm", "nth", "TV", "st", "ß", "straße", "ﬃ", "ﬂower", "ǳung", "ǰolt", "ΟΣ", "οσ", "ος", "σ", "ς", "İSTANBUL", "ıstanbul", "ſome", "Kelvin",
             "élève", "éclair", "áBC", "e\u0301clair", "中文", "हिन्दी", "日本語", "¼", "Ⅳ", "①", "𝔞𝔟", "𐐨𐐩", "😀", "👩‍💻", "ᾀ", "ῳ"]
    punctuation = ["", "", "", "'", '"', "[", "(", "{", "“", "‘", "!", "?", "\\", "_", "---"]
    closing = ["", "", "", "]", ")", "}", "'", '"', "”", "’", ".", ":", ";", "!", "?", ","]
    joiners = [" ", " ", " ", "  ", "\t", "\u00a0", "\u2003", "\x1f", "\u2028", " - ", " — ", ": ", "; "]
    parts = []
    for _ in range(rng.randint(1, 12)):
        token = rng.choice(words)
        kind = rng.randrange(7)
        if kind == 0:
            token = token + "-" + rng.choice(words)
        elif kind == 1:
            token = token + "/" + rng.choice(words)
        elif kind == 2:
            token = token + "//" + rng.choice(words)
        elif kind == 3:
            token = token + "-" + rng.choice(words) + "/" + rng.choice(words)
        parts.append(rng.choice(punctuation) + token + rng.choice(closing))
    title = parts[0]
    for token in parts[1:]:
        title += rng.choice(joiners) + token
    transform = rng.randrange(7)
    if transform == 0:
        title = title.upper()
    elif transform == 1:
        title = title.lower()
    elif transform == 2:
        title = " " + title + "  "
    elif transform == 3:
        title = "\t" + title
    return title


def corpus(source: Path) -> tuple[list[str], list[str]]:
    rng = random.Random(SEED)
    public: list[str] = []
    hidden: list[str] = []
    seen: set[str] = set()
    for value in fixed_inputs(source):
        if value in seen:
            continue
        if "\r" in value or "\n" in value:
            raise RuntimeError("An embedded record delimiter appeared in an input")
        seen.add(value)
        (public if len(seen) % 2 else hidden).append(value)
    while len(public) < COUNT or len(hidden) < COUNT:
        value = random_title(rng)
        if value in seen:
            continue
        seen.add(value)
        target = public if len(public) < COUNT and (len(public) <= len(hidden) or len(hidden) >= COUNT) else hidden
        target.append(value)
    return public, hidden


def as_bytes(records: list[str]) -> bytes:
    return b"".join(value.encode("utf-8") + b"\n" for value in records)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    task_root = Path(__file__).resolve().parents[1]
    parser.add_argument("--source", type=Path, default=task_root / "environment" / "repo")
    parser.add_argument("--output", type=Path, default=task_root / "tests" / "data")
    args = parser.parse_args()
    if sys.version_info[:2] != (3, 12):
        raise SystemExit("Use Python 3.12: python3.12 -S tests/gen.py")
    source = args.source.resolve()
    reference = reference_module(source)
    public, hidden = corpus(source)
    datasets = {"inputs.txt": public, "hidden_inputs.txt": hidden,
                "expected.txt": [reference.titlecase(v) for v in public],
                "hidden_expected.txt": [reference.titlecase(v) for v in hidden]}
    args.output.mkdir(parents=True, exist_ok=True)
    file_info = {}
    for name, records in datasets.items():
        if len(records) != COUNT or any("\r" in v or "\n" in v for v in records):
            raise RuntimeError(f"Invalid line-oriented fixture: {name}")
        payload = as_bytes(records)
        (args.output / name).write_bytes(payload)
        file_info[name] = {"records": len(records), "bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest(),
                           "max_record_bytes": max(map(lambda v: len(v.encode('utf-8')), records)), "blank_records": records.count("")}
    manifest = {"format": "UTF-8; LF-delimited records; one final LF; embedded CR/LF excluded; other characters preserved",
                "seed": SEED, "public_hidden_inputs_disjoint": True,
                "upstream": {"url": UPSTREAM_URL, "commit": UPSTREAM_SHA, "version": reference.__version__, "license": "MIT",
                             "source_file": "titlecase/__init__.py", "source_sha256": SOURCE_SHA256},
                "reference": {"function": "titlecase.titlecase(text)", "arguments": "defaults; no callback; no small-word-list modification",
                              "python": platform.python_version(), "implementation": platform.python_implementation(),
                              "unicode_version": unicodedata.unidata_version, "regex_backend": "stdlib re", "optional_regex_package": False},
                "files": file_info}
    (args.output / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"generated": len(file_info), "records_per_file": COUNT, "input_sets_disjoint": not set(public).intersection(hidden), "output": str(args.output)}, indent=2))


if __name__ == "__main__":
    main()

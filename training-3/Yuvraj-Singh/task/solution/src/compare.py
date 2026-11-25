"""Compare the Go port with python-titlecase on the library's own cases."""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PY_REPO = ROOT / "environment" / "python-titlecase"
sys.path.insert(0, str(PY_REPO))

from titlecase import titlecase  # noqa: E402
from titlecase.tests import TEST_DATA  # noqa: E402


def cases():
    seen = set()
    for src, _expected in TEST_DATA:
        for line in src.splitlines() or [""]:
            if line not in seen:
                seen.add(line)
                yield line
    extras = [
        "the lord of the rings",
        "a",
        "OF MICE AND MEN",
        "http://example.com/foo-bar",
        "and/or",
        "McDonald",
        "o'clock",
        "d'Angelo",
        "NASA is neat",
        "the SEC's probe: what you need to know",
        "foo: the bar",
        "A.B.C. initials",
        "U.S.A. TODAY",
        "   leading spaces",
        "trailing spaces   ",
        "double  space",
        "em—dash word",
        "it’s a test",
        "EL NIÑO",
        "",
        "v.",
        "vs.",
        "Q&A",
        "iPhone",
        "cnn",
        "HTML and CSS",
        "state-of-the-art",
        "well-known",
        "a/b/c",
        "Mr. and Mrs. Smith",
        "'QUOTE' A GREAT",
        "mccay-mcbut-mcdo mcdonalds/mcby",
        "l'GranGe",
        "O'GranGe",
        "o'grange's",
        "mac mc MAC MC machine",
        "ÝÆ ÑØ",
        "ýæ ñø",
        "a mix\u00a0of\tdifferent\u200aspace\u2006characters",
        "34th 3rd 2nd",
        "2lmc Spool",
        "AT&T",
        "at&t",
        "del.icio.us",
        "end of",
        "the",
        "A small Start",
        "word/word",
        "five-and",
        "Two-Not-Three/Three-by-Four/Five-And",
        "NOTHING TO BE AFRAID OF",
        '"Nothing to Be Afraid of?"',
        "WASHINGTON, D.C. SHOULD BE FIXED BUT MIGHT BE A PROBLEM",
        "EPISODE 7 — THE FORCE AWAKENS",
        "episode 7 – The force awakens",
        "THE CASE OF X ≤ 7",
        "“YOUNG AND RESTLESS”",
        "‘QUOTE’ A GREAT",
        "Mr mr Mrs Ms Mss Dr dr , Mr. and Mrs. Person",
        "oblon, spivak, mcclelland, maier & neustadt",
        "mcfoo-bar, MCFOO-BAR, McFoo-bar, McFoo-Bar, mcfoo-mcbar, foo-mcbar",
        "reading between the lines of steve jobs’s ‘thoughts on music’",
        "seriously, ‘repair permissions’ is voodoo",
        "this is http://foo.com",
        "this shouldn't",
        "get mangled",
        "FOO BAR 5TH ST",
        "foo bar 5th st",
        "YEA NO",
        "yea no",
    ]
    for line in extras:
        if line not in seen:
            seen.add(line)
            yield line


def main():
    lines = list(cases())
    payload = "\n".join(lines) + "\n"
    src = Path(__file__).resolve().parent
    proc = subprocess.run(
        [
            "docker", "run", "--rm", "-i",
            "-v", f"{src}:/src",
            "-w", "/src",
            "golang:1.23",
            "go", "run", ".",
        ],
        input=payload.encode("utf-8"),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode != 0:
        sys.stderr.write(proc.stderr.decode("utf-8", "replace"))
        sys.exit(proc.returncode)
    actual = proc.stdout.decode("utf-8").splitlines()
    # Keep a trailing empty line if present. splitlines() drops the final newline
    # but also drops a trailing empty line only when keepends is false and the
    # string ends with a newline — that drops one empty. Compare by expected list.
    mismatches = 0
    if len(actual) != len(lines):
        print(f"line count go={len(actual)} py_inputs={len(lines)}")
    for i, src in enumerate(lines):
        exp = titlecase(src)
        if "\n" in exp:
            print(f"MULTILINE unexpected for {src!r} -> {exp!r}")
            mismatches += 1
            continue
        got = actual[i] if i < len(actual) else "<missing>"
        if got != exp:
            mismatches += 1
            if mismatches <= 40:
                print("---")
                print(f"IN : {src!r}")
                print(f"PY : {exp!r}")
                print(f"GO : {got!r}")
    print(f"cases={len(lines)} mismatches={mismatches}")
    sys.exit(1 if mismatches else 0)


if __name__ == "__main__":
    main()

import argparse
import string
import subprocess
from pathlib import Path

from reference import ROOT, regex

PROPERTIES = (
    r"\p{Letter}", r"\p{Uppercase_Letter}", r"\w", r"\s",
    r"(?i:[bcdfghjklmnpqrstvwxz])",
)
PROPERTY_MATCHERS = tuple(regex.compile(pattern).fullmatch for pattern in PROPERTIES)
ASCII_CLASS = regex.compile(r"[a-z]", regex.I).fullmatch
ASCII_MATCHERS = tuple((ch, regex.compile(ch, regex.I).fullmatch)
                       for ch in string.ascii_lowercase)


def classify(ch):
    flags = sum(1 << index for index, match in enumerate(PROPERTY_MATCHERS) if match(ch))
    if ch.isascii():
        folded = ch.lower() if ch.isalpha() else ""
    elif ASCII_CLASS(ch):
        matches = [letter for letter, match in ASCII_MATCHERS if match(ch)]
        if len(matches) != 1:
            raise ValueError((ch, matches))
        folded = matches[0]
    else:
        folded = ""

    after_sigma = ("AΣ" + ch).lower()[1]
    before_cased = ("AΣ" + ch + "A").lower()[1]
    if after_sigma == "ς" and before_cased == "σ":
        flags |= 1 << 5
    if after_sigma == "σ":
        flags |= 1 << 6
    return flags, folded


def quote(value):
    return '"' + "".join(f"\\U{ord(ch):08X}" for ch in value) + '"'


def render():
    ranges, cases = [], []
    for code in range(0x110000):
        if 0xD800 <= code <= 0xDFFF:
            continue
        char = chr(code)
        flags, folded = classify(char)
        if flags or folded:
            if ranges and ranges[-1][1] == code - 1 and ranges[-1][2:] == (flags, folded):
                ranges[-1] = (ranges[-1][0], code, flags, folded)
            else:
                ranges.append((code, code, flags, folded))

        upper, lower, title = char.upper(), char.lower(), char.title()
        if (upper, lower, title) != (char, char, char):
            fields = [quote(value) if value != char else '""' for value in (upper, lower, title)]
            cases.append(f"\t0x{code:X}: {{{', '.join(fields)}}},")

    properties = [
        f"\t{{0x{first:X}, 0x{last:X}, {flags}, {ord(folded) if folded else 0}}},"
        for first, last, flags, folded in ranges
    ]
    return "\n".join([
        "package main", "", "var pythonProperties = [...]propertyRange{",
        *properties, "}", "", "var pythonCases = map[rune]caseMapping{",
        *cases, "}", "",
    ])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "solution/go/unicode_data.go")
    args = parser.parse_args()
    formatted = subprocess.run(
        ["gofmt"], input=render().encode("ascii"), capture_output=True, check=True
    )
    args.output.write_bytes(formatted.stdout)


if __name__ == "__main__":
    main()

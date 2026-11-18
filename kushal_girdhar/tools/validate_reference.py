import argparse
import hashlib
import json
from pathlib import Path
import random
import subprocess

from reference import ROOT, describe, framed, load

FRAGMENTS = (
    "A.", "A.BC.D", "J.KL.", "É.Y", "A.BC.DE", "A", "DR", "mRs", "mCcloud", "Mcmca",
    "mcmcmcthe", "mc猫σ", "mCA", "o'ßs'", "d'ς", "L‘ŉss'", "d'a''", "d's'", "o'a's",
    "o'𐐷ops", "d'os'", "D'2S'", "L'__'s", "d’água", "d'’a", "foo.bar", "_._", "1.᠑",
    "–", "—", "―", "‼", "?", ":", ";", "😀", "vs", "v.", "via", "v.ſ", "vſ.", "ın",
    "İf", "ſtr", "Krg", "ß", "ﬃ", "ǳ", "ᾀ", "ǰ", "ΐ", "և", "ΟΣ", "Σ", "ΑʰΣ",
    "Σ\u0345Α", "ΑΣ!", "ΑΣʰА", "ΑΣʰ", "𐐧", "𞤀", "𐑅", "_Alpha", "²", "𰻞",
    "a\u0345", "नमस्ते", "Հայ", "ﬓ", "ﷺ", "cCnd", "read//only", "/in--out-/", "y", "NY",
    "TCP", "ST", "and", "as", "at", "the", "on", "of", "a", "an", "in", "for", "the.",
    "a/an", "the-of-/", "//---///-", "the:", "—by", "‘(an", "_of", "ʰm", "\0",
)
SEPARATORS = (
    "", "-", "/", "//", "--", " ", " ", "  ", ":", ": ", " / ", "\t", "\v", "\x1f",
    "\x85", "\xa0", "\u1680", "\u2003", "\u2028", "\u2029", "\u202f", "\u205f", "\u3000",
)
BLOCKS = (
    (0, 0x7f), (0xc0, 0x52f), (0x1e00, 0x1fff), (0x2000, 0x218f), (0xa640, 0xa7ff),
    (0xfb00, 0xfb4f), (0x10400, 0x104ff), (0x1e900, 0x1e95f), (0x2f800, 0x2fa1f),
)


def stress(count):
    rng = random.Random(743681)
    for index in range(count):
        action = rng.randrange(8)
        if action < 4:
            record = "".join(
                rng.choice(FRAGMENTS) + rng.choice(SEPARATORS)
                for _ in range(rng.randrange(1, 13))
            ) + rng.choice(FRAGMENTS)
        elif action < 7:
            start, end = rng.choice(BLOCKS)
            ch = chr(rng.randint(start, end))
            if ch in "\r\n":
                ch = "§"
            layout = rng.choice(("{0} {1}", "{0}{1}", "AΣ{0}{1}", "A{0}Σ {1}", "o'{0}{1}", "mc{0}{1}", "a.{0} {1}"))
            record = layout.format(ch, rng.choice(FRAGMENTS))
        else:
            points = [rng.randrange(0x110000) for _ in range(rng.randrange(1, 12))]
            letters = "".join(chr(ch) for ch in points if not 0xd800 <= ch <= 0xdfff and ch not in (10, 13))
            record = rng.choice(FRAGMENTS) + rng.choice(SEPARATORS) + letters
        yield record.upper() if index % 3 == 0 else record


def records(payload):
    assert payload.endswith(b"\n")
    return payload[:-1].decode("utf-8").split("\n")


def compare(binary, rows, actual_input, expected_output):
    result = subprocess.run([binary], input=actual_input, capture_output=True, check=True, timeout=180)
    if result.stderr:
        raise AssertionError(f"unexpected stderr: {result.stderr[:1000]!r}")
    if result.stdout != expected_output:
        actual = result.stdout.split(b"\n")
        expected = expected_output.split(b"\n")
        mismatches = []
        for index in range(max(len(actual), len(expected))):
            got = actual[index:index+1]
            wanted = expected[index:index+1]
            if got != wanted:
                mismatches.append((index, rows[index:index+1], wanted, got))
            if len(mismatches) == 10:
                break
        raise AssertionError(ascii(mismatches))
    return hashlib.sha256(result.stdout).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("binary", type=Path)
    parser.add_argument("--count", type=int, default=120_000)
    args = parser.parse_args()
    binary = args.binary.resolve(strict=True)
    reference = load()
    print(json.dumps(describe()), flush=True)
    data = ROOT / "tests" / "data"
    slices = []
    for label in ("", "hidden_"):
        input_data = (data / (label + "inputs.txt")).read_bytes()
        expected = (data / (label + "expected.txt")).read_bytes()
        rows = records(input_data)
        outputs = records(expected)
        assert len(rows) == len(set(rows)) == len(outputs) == len(set(outputs)) == 2000
        assert framed(map(reference, rows)) == expected
        slices.append((set(rows), set(outputs)))
        print(f"{label or 'visible'}: 2,000 frozen answers verified and matched; stdout SHA256 "
              f"{compare(binary, rows, input_data, expected)}", flush=True)
        if not label:
            for index in (0, 463, 911, 1487, 1999):
                print(f"spot check {index+1}: {ascii(rows[index])} -> {ascii(reference(rows[index]))}")
    assert slices[0][0].isdisjoint(slices[1][0]) and slices[0][1].isdisjoint(slices[1][1])
    print("split overlap: 0 inputs, 0 outputs", flush=True)
    protocol = [
        ([], b""), ([""], b"\n"), (["", ""], b"\r\n\n"),
        ([" the cache", "", "route/of/return"], b" the cache\r\n\r\nroute/of/return"),
        (["a\tb", "x\u2028y", "z\x85w", "Σ\0α"], "a\tb\nx\u2028y\r\nz\x85w\nΣ\0α\n".encode()),
        (["by", "", "  "], b"by\n\r\n  "),
        (["node " * 100_000 + "ß"], ("node " * 100_000 + "ß").encode()),
        (["a-" * 90_000 + "of"], ("a-" * 90_000 + "of\r\n").encode()),
    ]
    for rows, payload in protocol:
        compare(binary, rows, payload, framed(map(reference, rows)))
    print(f"protocol: {len(protocol)} byte-exact cases", flush=True)
    rows = list(stress(args.count))
    expected = framed(map(reference, rows))
    print(f"independent stress: {len(rows):,} records, {len(set(rows)):,} distinct, zero mismatches; stdout SHA256 "
          f"{compare(binary, rows, framed(rows), expected)}", flush=True)


if __name__ == "__main__":
    main()

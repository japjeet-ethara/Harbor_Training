import random
import subprocess
import sys

from reference import lf_records, record_bytes, titlecase

RNG = random.Random(193512)
TRAPS = (
    "and", "as", "at", "in", "of", "on", "the", "v.", "via", "vs.", "ın", "İn",
    "OF", "İF", "aſ", "K", "ß", "ﬃ", "ǳ", "A.A.", "B.CD.A", "Α.Β", "J.P.Q.",
    "mR", "dR", "mſ", "O'neil's", "D'abc''", "d‘ſſ", "D'ΣΣ", "D'ﬃl",
    "Mc", "mC", "MC", "McMcAnd", "mc_of", "mc𐐨r", "mcɑ", "mcof-", "mc-to",
    "mcand/of", "mcd'água", "eBay", "ǅand", "Ǆand", "a.B", "3.a", "a.𐐨",
    "a\u0301.a", "Ａ.Ｂ", "brr", "ţş", "ſſſ", "æ", "ΛΟΓΟΣ", "Σ\u0345",
    "ΟΣ\u200d", "Σ\u0301Σ", "Σ\u0345A", "ᲐᲜᲑᲐᲜᲘ", "ᲃ", "𐐨", "𞤢",
    "of\u200d", "the\u0301", "of\u203f", "𞤢and", "to_", "in_", "as✧",
    "in//out", "x--in", "in/and-of", ";;", "“", "’", "¿", "¡", "÷", "🠮",
)
GLUE = (" ", "", "/", "//", "-", "--", ":", ": ", "? ", "— ", "‒ ", ". ", "  ",
        "\t", "\v", "\f", "\x1c", "\x1f", "\u0085", "\u2002", "\u2009", "\u200b",
        "\u200c", "\u2028", "\u2029", "\u00a0", "\u0301", "'", "_", "9", ".")
CATEGORIES = (
    (0x00C0, 0x0250), (0x0250, 0x0370), (0x0370, 0x0400), (0x0400, 0x0530),
    (0x0590, 0x0700), (0x0900, 0x0A80), (0x10A0, 0x1100), (0x1C80, 0x1CC0),
    (0x1E00, 0x2000), (0x2000, 0x2200), (0xFB00, 0xFB50), (0x10400, 0x10500),
    (0x1C800, 0x1CA00), (0x1E900, 0x1E960), (0x10000, 0x110000),
)


def codepoint():
    low, high = RNG.choice(CATEGORIES)
    return chr(RNG.randrange(low, high))


def case(index):
    family = index % 6
    if family == 0:
        values = RNG.choices(TRAPS, k=RNG.randrange(3, 10))
        value = values[0] + "".join(RNG.choice(GLUE) + item for item in values[1:])
    elif family == 1:
        value = RNG.choice(TRAPS) + "".join(codepoint() for _ in range(RNG.randrange(2, 8)))
        value += RNG.choice(GLUE) + RNG.choice(TRAPS)
    elif family == 2:
        value = ("Mc" * RNG.randrange(1, 7) + RNG.choice(TRAPS) +
                 RNG.choice(("/", "-", "/-", "-/", "//", "--")) + RNG.choice(TRAPS) +
                 " " + RNG.choice(TRAPS) + RNG.choice(("?", ": ", "— ", "; ")) +
                 RNG.choice(TRAPS))
    elif family == 3:
        value = (RNG.choice(TRAPS) + RNG.choice(GLUE) + RNG.choice(("Σ", "ΣΣ", "Σ\u0345")) +
                 "".join(codepoint() for _ in range(3)) + " " + RNG.choice(TRAPS))
    elif family == 4:
        value = (RNG.choice(("\\", "_", "!", "[", "]", "—", "”", "‘", "\x60", "©")) +
                 RNG.choice(TRAPS) + RNG.choice(GLUE) + RNG.choice(TRAPS) + RNG.choice(GLUE) +
                 RNG.choice(TRAPS) + RNG.choice(("", "_", "!", "\u0301", ".", "\u200d")))
    else:
        alphabet = "aiAvsftbdMCΩΣ.\u2060-/'&ßŒᲐø九"
        value = "".join(RNG.choices(alphabet, k=RNG.randrange(3, 26)))
        value += RNG.choice(GLUE) + RNG.choice(TRAPS)
    mode = RNG.randrange(8)
    return value.upper() if mode == 0 else value.lower() if mode == 1 else value


def verify(executable, count):
    seen = set()
    inputs = []
    while len(inputs) < count:
        candidate = case(len(inputs))
        if candidate not in seen:
            seen.add(candidate)
            inputs.append(candidate)

    expected = record_bytes(titlecase(item) for item in inputs)
    run = subprocess.run([executable], input=record_bytes(inputs), capture_output=True,
                         timeout=120, check=True)
    if run.stdout != expected:
        wanted, actual = lf_records(expected), lf_records(run.stdout)
        failures = 0
        for source, expected, observed in zip(inputs, wanted, actual, strict=True):
            if expected != observed:
                if failures < 24:
                    print(repr(source), repr(expected.decode()), repr(observed.decode()))
                failures += 1
        raise SystemExit(f"{failures:,} of {count:,} differential cases failed")
    print(f"{count:,} unique independent differential cases matched byte for byte (seed 193512)")


if __name__ == "__main__":
    verify(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 120_000)

"""Write string-level casing cases from the reference interpreter.

Usage: python -I -B mkhelpercases.py <out.tsv>
Each row: input, str.upper(), str.lower(), str.capitalize(), all as hex code point
lists. Includes every <c1> Σ <c2> triple over the alphabet (final-sigma context),
plus 30,000 random strings (seed 1).
"""
import random
import sys

ALPHABET = [
    "Σ", "σ", "ς", "A", "a", "b", "Z", " ", "'", ".", ":", "-", "_", "1",
    "ʰ",            # MODIFIER LETTER SMALL H: Lm and Other_Lowercase (cased and ignorable)
    "́", "̇",  # combining marks (Mn)
    "­",            # SOFT HYPHEN (Cf)
    "ͅ",            # COMBINING GREEK YPOGEGRAMMENI (Mn, Other_Lowercase)
    "ᾳ", "ᾼ",  # ᾳ, ᾼ (titlecase letter)
    "Ǆ", "ǅ", "ǆ",  # Ǆ ǅ ǆ
    "İ", "ı", "i", "I",  # İ ı i I
    "ß", "ẞ",  # ß ẞ
    "ﬁ", "ﬂ", "ﬃ", "ﬆ",  # ﬁ ﬂ ﬃ ﬆ
    "ŉ", "ΐ", "և",  # ŉ ΐ և
    "K", "Ω",  # KELVIN SIGN, OHM SIGN
    "’", "·", "ꭜ",
    "Ⓐ", "ⓐ",  # Ⓐ ⓐ (So, Other_Uppercase / Other_Lowercase)
    "\U00010d50", "\U00010d70",  # Garay capital/small (Unicode 16.0)
    "Ᲊ", "ᲊ",  # Cyrillic TJE (Unicode 16.0)
    "\U0001171e",        # AHOM CONSONANT SIGN MEDIAL RA (Mn in 15.0, Mc in 16.0)
    "\U0001e944",        # ADLAM ALIF LENGTHENER (Mn)
]


def hexseq(s):
    return " ".join(f"{ord(c):X}" for c in s)


def main():
    cases = []
    for a in ALPHABET:
        for b in ALPHABET:
            cases.append(a + "Σ" + b)
    rng = random.Random(1)
    for _ in range(30000):
        cases.append("".join(rng.choice(ALPHABET) for _ in range(rng.randint(1, 8))))
    with open(sys.argv[1], "w", encoding="ascii", newline="\n") as f:
        f.write(f"# python {sys.version.split()[0]}\n")
        for s in cases:
            f.write(f"{hexseq(s)}\t{hexseq(s.upper())}\t{hexseq(s.lower())}\t{hexseq(s.capitalize())}\n")
    print(f"helper cases {len(cases)} (alphabet {len(ALPHABET)})")


if __name__ == "__main__":
    main()

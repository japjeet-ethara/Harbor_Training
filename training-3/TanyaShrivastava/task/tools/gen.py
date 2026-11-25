#!/usr/bin/env python3
"""Generate the Harbor task's test data.

Author-only tool (NOT shipped to the agent or to the verifier image).

    python3 tools/gen.py [--repo ../python-titlecase]

Writes four files into tests/data/:
    inputs.txt, expected.txt              (visible set - for the author / debugging)
    hidden_inputs.txt, hidden_expected.txt (the set the verifier grades on)

Every expected line is produced by running the ORIGINAL Python
``titlecase()`` (with the optional ``regex`` package installed, which is the
reference behaviour). Nobody writes expected answers by hand.
"""
import argparse
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TASK = os.path.dirname(HERE)
N = 2000

# --------------------------------------------------------------------------
# Vocabulary. Each pool targets one rule of the original implementation.
# --------------------------------------------------------------------------
PLAIN = """lord rings quick brown fox jumps over lazy dog war peace tale cities great
expectations journey centre earth hobbit adventure data science python guide
beginner modern web design patterns story night day city river mountain garden
silent whisper broken promise winter summer ocean engine machine learning
history empire fall rise secret letters house stone bridge thunder shadow
light darkness voyage island treasure dragon kingdom queen king prince tower
music painting theatre cinema poetry novel essay review notes manual handbook
introduction chapter summary conclusion analysis report future past present
sunrise sunset harvest festival market village castle forest valley desert
ancient medieval renaissance revolution industrial digital analog quantum""".split()

SMALL = ["a", "an", "and", "as", "at", "but", "by", "en", "for", "if", "in", "of",
         "on", "or", "the", "to", "v", "v.", "via", "vs", "vs."]
SMALL_BAD = ["A", "An", "AND", "As", "AT", "But", "BY", "En", "FOR", "If", "In", "Of",
             "ON", "Or", "The", "TO", "V", "V.", "Via", "VS", "Vs."]
# words that merely START like a small word (SUBPHRASE has no word boundary)
SMALL_PREFIX = ["another", "answer", "about", "after", "again", "always", "any",
                "bylaw", "button", "buttery", "enough", "entry", "format", "forest",
                "ifs", "infinite", "inside", "often", "online", "order", "other",
                "theory", "their", "today", "together", "vessel", "virtue", "vsync",
                "viaduct", "organ", "island", "anthem", "asset", "atlas"]

ACRONYM = ["pdf", "html", "css", "nyc", "sql", "cpp", "ftp", "ssh", "http", "xml",
           "rpm", "cpu", "gpu", "ram", "dns", "tcp", "bmw", "ibm", "nbc", "hmm",
           "tv", "st", "ms", "mr", "wtf", "cd", "dvd", "jpg", "png", "xyz", "rhythm",
           "nth", "pst", "gmbh", "strength"]

MAC = ["mcdonald", "McDonald", "MCDONALD", "mcgregor", "McGregor", "mcallister",
       "MCALLISTER", "Mccoy", "mcdonald's", "mcdonalds", "mcon", "mc", "Mc", "mcx",
       "mcintosh", "macdonald", "macbeth", "mcdonald-smith", "McDONALD", "mc-donald",
       "mc2", "mc_x", "mc.x", "Mc'Donald", "mcAllister", "mcdOnald", "mcthe", "mcof"]

HONORIFIC = ["mr", "MR", "Mr", "mR", "mrs", "MRS", "Mrs", "ms", "MS", "Ms", "dr", "DR",
             "Dr", "dR", "mr.", "dr.", "ms.", "mrs.", "Dr.", "mr-smith", "dr/who",
             "mrx", "drs", "mss"]

APOS = ["d'artagnan", "D'Artagnan", "o'neil", "O'Neil", "O'NEIL", "l'amour", "L'Amour",
        "d'angelo", "D'ANGELO", "o'brien's", "o'neil's", "l'été", "d‘artagnan",
        "o‘neil", "l‘amour", "d'a", "d'", "o'", "d'x'", "d'ab's", "O'ss", "d'abss",
        "o'neill''", "d'x1", "d'1x", "d’artagnan", "o’neil", "l’amour", "x'neil",
        "a'neil", "i'm", "don't", "isn't", "rock'n'roll", "d'artagnan-smith", "L'Été"]

INITIALS = ["J.R.R.", "U.S.A.", "A.B.", "J.K.", "U.S.", "A.B.C", "a.b.", "J.R.R", "T.S.",
            "A.", "A.B.C.D.", "X.Y", "E.T.", "A..B", "A.b.", "J.r.r.", "Q.E.D.", "N.A.S.A",
            "A.B.C.D", "Z.", "É.É.", "A.É."]

INLINE_PERIOD = ["example.com", "node.js", "e.g.", "i.e.", "file.txt", "Ph.D.", "ph.d",
                 "www.site.org", "a.b", "v1.2", "3.14", "1.x", "x.1", "e.g", "a.m.",
                 "p.m.", "u.s.", "Dr.Who", "mr.smith", "the.end", "of.the", "to.do",
                 "a.b.c", "é.à", "x.", ".x", "...", "end.", "(e.g.", "e.g.)", "etc."]

MIXED = ["iPhone", "eBay", "macOS", "YouTube", "PowerPoint", "iOS", "McAfee", "LaTeX",
         "GitHub", "JavaScript", "pH", "mRNA", "iPad", "tvOS", "xBox", "dB", "kHz",
         "aB", "aBc", "Ab", "AB", "ABc", "aBC", "ÉcoLe", "éCole", "(iPhone)", "'eBay'",
         "-iPhone", "1iPhone", "i1Phone", "iPhone's", "x-Ray", "eBay/PayPal", "a.B"]

COMPOUND = ["and/or", "client/server", "state-of-the-art", "e-mail", "x-ray", "a-b",
            "to-do", "over-the-top", "re-use/recycle", "a/b-testing", "//cdn", "http://x",
            "a//b", "word-", "-word", "/word", "word/", "a-", "-a", "to-the", "in/out",
            "the-end", "for/of", "x-the-y", "long-term/short-term", "up-to-date",
            "A-B", "HELLO-world", "WORLD-ART", "ALPHA/BETA", "Alpha-BETA", "pre-war-era",
            "one-to-one", "a--b", "a-/-b", "of-", "-of", "the/", "/the", "vs-the",
            "co-op", "t-shirt", "x/y/z", "mid-century/modern", "on-and-off", "by-the-by"]

PUNCTWORD = ["(the)", "\"quoted\"", "‘single’", "“curly”", "[brackets]", "{braces}",
             "...", "—", "–", "-", ":", ";", "?", "!", "word,", "word.", "(a)", "'a'",
             "“the”", "‘an’", "(in)", "[of]", "—the—", "(vs.)", "a,", "the.", "of!",
             "by?", "at;", "to:", "in)", "(to", "a’", "of”", "’a", "”the", "@a", "#the",
             "$to", "%of", "&in", "*or", "+by", "_a_", "~the~", "`as`", "|if|",
             "\\the", "^the", "<the>", "=of", "3a", "a3", "(3", "-5", "2024", "10x",
             "1st", "42", "0", "°", "§", "¿qué?", "¡hola!"]

UNICODE = ["café", "naïve", "über", "ÀÉÎ", "Łódź", "Žižek", "Ñandú", "øre", "élan",
           "École", "ÉCOLE", "œuvre", "ŒUVRE", "çà", "ÇA", "ÿ", "Ÿ", "ñ", "Ñ", "þorn",
           "Þorn", "ðe", "Ðe", "æon", "ÆON", "ĳ", "Ĳ",
           "ťa", "ŤA", "łódź-łódź", "über/école", "café-au-lait", "à-la-carte", "ÉTÉ-été",
           "(été)", "«the»", "„of“", "‚a‘"]

SPACES = [" "] * 40 + ["  ", "   ", "\t", " \t ", "\u00a0", "\u2003", "\u2009", "\u3000", "\u2002"]

SUBPHRASE_SEPS = [": ", ". ", "; ", "? ", "! ", " - ", " – ", " — ", " ‒ ", " ― ", "- ", "– ",
                  ":  ", ":\t", ": \u00a0", ":", ". .", "; ;"]


def pick(pool):
    return random.choice(pool)


def body_word():
    """One 'ordinary' word drawn from the weighted pools."""
    r = random.random()
    if r < 0.38:
        return pick(PLAIN)
    if r < 0.54:
        return pick(SMALL)
    if r < 0.56:
        return pick(SMALL_BAD)
    if r < 0.60:
        return pick(SMALL_PREFIX)
    if r < 0.64:
        return pick(ACRONYM)
    if r < 0.68:
        return pick(MAC)
    if r < 0.71:
        return pick(HONORIFIC)
    if r < 0.75:
        return pick(APOS)
    if r < 0.78:
        return pick(INITIALS)
    if r < 0.82:
        return pick(INLINE_PERIOD)
    if r < 0.86:
        return pick(MIXED)
    if r < 0.92:
        return pick(COMPOUND)
    if r < 0.96:
        return pick(PUNCTWORD)
    return pick(UNICODE)


def restyle(word):
    r = random.random()
    if r < 0.55:
        return word
    if r < 0.70:
        return word.capitalize() if random.random() < .5 else word.title()
    if r < 0.82:
        return word.upper()
    if r < 0.90:
        return word.lower()
    if r < 0.95:
        return word[:1].upper() + word[1:]
    # random case per character
    return "".join(c.upper() if random.random() < .5 else c.lower() for c in word)


def sentence():
    n = random.choice([1, 1, 2, 2, 3, 3, 4, 5, 6, 7, 8, 10, 12])
    mode = random.random()
    parts = []
    for i in range(n):
        w = body_word()
        if mode < 0.30:
            w = restyle(w)
        elif mode < 0.45:
            w = w.upper()
        elif mode < 0.60:
            w = w.capitalize()
        parts.append(w)
        if i < n - 1:
            if random.random() < 0.12:
                # a sub-phrase separator, then (often) a small word / small-prefix
                parts.append(pick(SUBPHRASE_SEPS))
                parts.append(pick(SMALL + SMALL_PREFIX + PLAIN))
                parts.append(" ")
            else:
                parts.append(pick(SPACES))
    s = "".join(parts)
    # all-caps line (lets `all_caps` mode kick in for many rule paths)
    r = random.random()
    if r < 0.12:
        s = s.upper()
    elif r < 0.16:
        s = s.lower()
    # stray leading / trailing whitespace
    r = random.random()
    if r < 0.03:
        s = " " + s
    elif r < 0.06:
        s = s + " "
    elif r < 0.07:
        s = "\t" + s
    return s


def bad_chars(s):
    # keep lines strictly one-per-line and inside the documented alphabet
    return any(c in s for c in "\r\n\x0b\x0c\x1c\x1d\x1e\x1f\x85\u2028\u2029")


def make_inputs(n, forbid=()):
    seen = set(forbid)
    out = []
    while len(out) < n:
        s = sentence()
        if not s.strip() or bad_chars(s) or s in seen:
            continue
        seen.add(s)
        out.append(s)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=os.path.join(TASK, "..", "python-titlecase"))
    ap.add_argument("--out", default=os.path.join(TASK, "tests", "data"))
    args = ap.parse_args()

    sys.path.insert(0, os.path.abspath(args.repo))
    import titlecase as tcmod
    if not tcmod.REGEX_AVAILABLE:
        sys.exit("The reference behaviour needs the `regex` package: pip install regex")

    os.makedirs(args.out, exist_ok=True)
    random.seed(1)
    visible = make_inputs(N)
    hidden = make_inputs(N, forbid=visible)  # disjoint from the visible set

    def write(name, lines):
        with open(os.path.join(args.out, name), "w", encoding="utf-8", newline="\n") as f:
            for ln in lines:
                f.write(ln + "\n")

    for in_name, ex_name, data in (("inputs.txt", "expected.txt", visible),
                                   ("hidden_inputs.txt", "hidden_expected.txt", hidden)):
        write(in_name, data)
        write(ex_name, [tcmod.titlecase(x) for x in data])
    print("regex module:", getattr(__import__("regex"), "__version__", "?"),
          "| titlecase", tcmod.__version__)
    print("wrote", N, "visible +", N, "hidden lines to", os.path.abspath(args.out))


if __name__ == "__main__":
    main()

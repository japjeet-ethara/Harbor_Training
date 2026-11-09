#!/usr/bin/env python3
import random
import sys
from pathlib import Path

# Original repo only. tests/gen.py -> titlecase-go -> sibling python-titlecase.
script_dir = Path(__file__).resolve().parent


def _load_titlecase():
    repo_dir = script_dir.parent.parent / "python-titlecase"
    init_py = repo_dir / "titlecase" / "__init__.py"
    if not init_py.is_file():
        raise RuntimeError(f"Original python-titlecase not found at {repo_dir}")

    sys.path.insert(0, str(repo_dir))
    from titlecase import titlecase
    import titlecase as titlecase_module

    if Path(titlecase_module.__file__).resolve() != init_py.resolve():
        raise RuntimeError(
            f"Imported {titlecase_module.__file__}, expected {init_py}"
        )
    return titlecase, titlecase_module

NOUNS = [
    "journey", "star", "war", "galaxy", "knight", "shadow", "light", "history",
    "world", "future", "chronicles", "song", "fire", "ice", "city", "secret",
    "legend", "empire", "heart", "storm", "wind", "ocean", "river", "mountain",
    "dragon", "sword", "king", "queen", "prince", "princess", "hero", "villain",
    "quest", "time", "space", "dimension", "portal", "mirror", "dream", "nightmare",
    "code", "algorithm", "compiler", "system", "network", "protocol", "agent",
    "model", "data", "benchmark", "matrix", "core", "spark", "echo", "dawn"
]

ADJECTIVES = [
    "dark", "bright", "ancient", "lost", "brave", "silent", "wild", "crimson",
    "golden", "iron", "frozen", "hidden", "broken", "eternal", "forgotten",
    "epic", "final", "first", "last", "great", "quiet", "new", "old", "deep"
]

SMALL_WORDS = [
    "a", "an", "and", "as", "at", "but", "by", "en", "for", "if", "in", "of",
    "on", "or", "the", "to", "v.", "v", "via", "vs.", "vs"
]

MAC_MC = [
    "mcdonald", "mccarthy", "mcintosh", "macarthur", "macintyre",
    "mcgregor", "mcneil", "mcmillan", "mcclure", "mcdowell", "mc"
]

HONORIFICS = ["mr", "mrs", "ms", "dr", "dr smith", "mr jones", "mrs davis"]

APOS_SECOND = [
    "d'artagnan", "o'brien", "l'oreal", "o'connor", "d'angelo", "l'enfer",
    "o'reilly", "d'amato"
]

UC_INITIALS = ["u.s.a.", "u.k.", "f.b.i.", "c.i.a.", "n.a.s.a.", "a.i.", "e.u.", "w.h.o.", "u.n."]

INLINE_PERIODS = ["e.g.", "i.e.", "ph.d.", "amazon.com", "google.com", "node.js", "vue.js", "github.io"]

CAMEL_CASE = ["iPhone", "iPad", "eBay", "YouTube", "macOS", "OpenAI", "JavaScript", "TypeScript", "PlayStation"]

ACRONYMS = ["cnn", "bbc", "html", "xml", "fbi", "nsa", "sql", "css", "http", "json", "pdf", "sdk", "png", "svg", "cpu", "gpu"]

SHORT_CONSONANTS = ["st", "tv"]

HYPHENATED = [
    "high-quality", "low-budget", "jack-of-all-trades", "state-of-the-art",
    "user-friendly", "well-known", "part-time", "real-time", "full-scale"
]

SLASHED = [
    "left/right", "either/or", "input/output", "tcp/ip", "client/server",
    "read/write", "on/off", "true/false"
]

URLS = [
    "http://example.com", "https://harborframework.com/docs",
    "http://news.bbc.co.uk", "https://github.com/ppannuto/python-titlecase",
    "ftp://files.archive.org/data"
]

PUNCT_PAIRS = [('"', '"'), ("'", "'"), ("(", ")"), ("[", "]")]


def generate_title(rng):
    pattern_type = rng.randint(1, 14)

    if pattern_type == 1:
        # Standard phrase: small word start, adjectives, nouns, small word mid
        parts = [
            rng.choice(SMALL_WORDS),
            rng.choice(ADJECTIVES),
            rng.choice(NOUNS),
            rng.choice(SMALL_WORDS),
            rng.choice(NOUNS)
        ]
        return " ".join(parts)

    elif pattern_type == 2:
        # Subphrase with colon, semicolon, or dash
        p1 = f"{rng.choice(NOUNS)} {rng.choice(SMALL_WORDS)} {rng.choice(NOUNS)}"
        sep = rng.choice([":", ";", " —", " -"])
        p2 = f"{rng.choice(SMALL_WORDS)} {rng.choice(ADJECTIVES)} {rng.choice(NOUNS)}"
        return f"{p1}{sep} {p2}"

    elif pattern_type == 3:
        # Mac/Mc and honorifics
        mc = rng.choice(MAC_MC)
        h = rng.choice(HONORIFICS)
        n = rng.choice(NOUNS)
        return f"{h} meets {mc} in the {n}"

    elif pattern_type == 4:
        # Apostrophe second letter (d'artagnan, o'brien, l'oreal)
        apos = rng.choice(APOS_SECOND)
        n = rng.choice(NOUNS)
        s = rng.choice(SMALL_WORDS)
        return f"{apos} {s} {n}"

    elif pattern_type == 5:
        # Acronyms and UC initials
        acr = rng.choice(ACRONYMS)
        init = rng.choice(UC_INITIALS)
        n = rng.choice(NOUNS)
        return f"the {acr} and {init} report on {n}"

    elif pattern_type == 6:
        # Inline periods and camelCase
        ip = rng.choice(INLINE_PERIODS)
        cc = rng.choice(CAMEL_CASE)
        n = rng.choice(NOUNS)
        return f"using {cc} with {ip} for {n}"

    elif pattern_type == 7:
        # Hyphenated and slashed words
        hy = rng.choice(HYPHENATED)
        sl = rng.choice(SLASHED)
        n = rng.choice(NOUNS)
        return f"{hy} guide to {sl} {n}"

    elif pattern_type == 8:
        # Small word at end
        s = rng.choice(["for", "to", "in", "by", "of", "on", "with", "vs."])
        adj = rng.choice(ADJECTIVES)
        n = rng.choice(NOUNS)
        punct = rng.choice(["", "?", "!", "."])
        return f"what is the {adj} {n} {s}{punct}"

    elif pattern_type == 9:
        # Punctuation wrapped at start
        pair = rng.choice(PUNCT_PAIRS)
        s = rng.choice(SMALL_WORDS)
        n1 = rng.choice(NOUNS)
        n2 = rng.choice(NOUNS)
        return f"{pair[0]}{s} {n1}{pair[1]} and the {n2}"

    elif pattern_type == 10:
        # URLs
        url = rng.choice(URLS)
        n = rng.choice(NOUNS)
        return f"visit {url} for {n}"

    elif pattern_type == 11:
        # All caps line
        n1 = rng.choice(NOUNS).upper()
        n2 = rng.choice(NOUNS).upper()
        s = rng.choice(["AND", "OF", "THE", "IN", "FOR"])
        init = rng.choice(["U.S.A.", "N.A.S.A.", "F.B.I.", "A.I."])
        return f"THE {n1} {s} {n2}: {init} TODAY"

    elif pattern_type == 12:
        # Short consonant word (st / tv) vs Acronym
        short_c = rng.choice(SHORT_CONSONANTS)
        acr = rng.choice(ACRONYMS)
        n = rng.choice(NOUNS)
        return f"crossing the {short_c} bridge to see {acr} on {n}"

    elif pattern_type == 13:
        # Multiple spaces and special formatting
        w1 = rng.choice(ADJECTIVES)
        w2 = rng.choice(NOUNS)
        w3 = rng.choice(NOUNS)
        spaces = "  " if rng.random() < 0.5 else "   "
        return f"{w1}{spaces}{w2} and {w3}"

    else:
        # Tricky cases from NOTES.md
        tricky = [
            "team a vs. team b",
            "smith v. jones",
            "MCDONALD'S RESTAURANT",
            "MC HAMMER TIME",
            "by the st bridge",
            "l'oreal is a brand",
            "chapter one: a new hope",
            "first part; the sequel",
            "hello— the world",
            "jack-of-all-trades",
            "either/or",
            "the iPhone and iPad era",
            "high-quality low-budget film",
            "\"the start of something\"",
            "TESTING U.S.A. TODAY",
            "the cnn and bbc report"
        ]
        chosen = rng.choice(tricky)
        if rng.random() < 0.5:
            return f"{chosen}: {rng.choice(ADJECTIVES)} {rng.choice(NOUNS)}"
        return chosen


def main():
    titlecase, titlecase_module = _load_titlecase()
    random.seed(1)
    # Generate 2000 visible inputs
    inputs = [generate_title(random) for _ in range(2000)]
    # Generate 2000 hidden inputs (sequential continuation)
    hidden_inputs = [generate_title(random) for _ in range(2000)]

    # Check for any newlines inside titles
    for title in inputs + hidden_inputs:
        if "\n" in title or "\r" in title:
            raise ValueError("Title contains newline!")

    data_dir = script_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    inputs_path = data_dir / "inputs.txt"
    expected_path = data_dir / "expected.txt"
    hidden_inputs_path = data_dir / "hidden_inputs.txt"
    hidden_expected_path = data_dir / "hidden_expected.txt"

    with open(inputs_path, "w", encoding="utf-8", newline="\n") as f_in, open(expected_path, "w", encoding="utf-8", newline="\n") as f_exp:
        for inp in inputs:
            exp = titlecase(inp)
            f_in.write(inp + "\n")
            f_exp.write(exp + "\n")

    with open(hidden_inputs_path, "w", encoding="utf-8", newline="\n") as f_in, open(hidden_expected_path, "w", encoding="utf-8", newline="\n") as f_exp:
        for inp in hidden_inputs:
            exp = titlecase(inp)
            f_in.write(inp + "\n")
            f_exp.write(exp + "\n")

    print(f"titlecase_file={titlecase_module.__file__}")
    print(f"Generated {len(inputs)} visible inputs/expected.")
    print(f"Generated {len(hidden_inputs)} hidden inputs/expected.")


if __name__ == "__main__":
    main()

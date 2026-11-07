#!/usr/bin/env python3
"""
Generate test titles and expected outputs for titlecase testing.
Uses random.seed(1) so it always produces the same output.
Generates 2000 titles into tests/data/inputs.txt and a different 2000 into tests/data/hidden_inputs.txt.
Mixes normal words with tricky cases derived from NOTES.md rules and input examples:

RULES AND INPUT EXAMPLES FROM NOTES.md:
1. Callback Rule: "tcp and udp"
2. All-Caps Uppercase Initials Preservation Rule: "WASHINGTON, D.C. SHOULD BE FIXED"
3. Apostrophe Contraction / Name Prefix Rule (APOS_SECOND): "my name is o'reilly and l'grange"
4. Scottish / Irish Name Prefix Rule (MAC_MC): "mcdonalds and mactavish"
5. Honorifics / Titles Rule (MR_MRS_MS_DR): "mr and dr smith"
6. Inline Period and Existing Uppercase Rule (INLINE_PERIOD & UC_ELSEWHERE): "this is example.com with iTunes"
7. Small Words Lowercasing Rule (SMALL_WORDS): "War And Peace"
8. Slash-Delimited Terms Rule: "a title and/or string"
9. Hyphen-Delimited Terms Rule: "a-b end-to-end two-not-three"
10. All-Consonant Acronyms Rule: "words with all consonants like cnn are acronyms"
11. General First-Letter Capitalization Rule (CAPFIRST): "hello world"
12. First Word Small Word Capitalization Rule (SMALL_FIRST): "a simple test"
13. Last Word Small Word Capitalization Rule (SMALL_LAST): "nothing to be afraid of"
14. Subphrase Capitalization Following Punctuation Rule (SUBPHRASE): "starting sub-phrase: a trick, perhaps?"

Runs the ORIGINAL Python titlecase() from ../python-titlecase on every line and
writes the results to tests/data/expected.txt and tests/data/hidden_expected.txt.
"""

import os
import random
import sys
from pathlib import Path

# Add python-titlecase to sys.path to run the original titlecase implementation
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_DIR = SCRIPT_DIR.parent.parent / "python-titlecase"
sys.path.insert(0, str(REPO_DIR))

try:
    from titlecase import titlecase
except ImportError as e:
    raise RuntimeError(f"Could not import titlecase from {REPO_DIR}: {e}")

# Exact tricky examples and fragments from NOTES.md rules:
NOTES_TRICKY_CASES = [
    # Rule 2: All-caps uppercase initials
    "WASHINGTON, D.C.", "D.C.", "A.B.", "U.S.", "Ph.D.", "N.Y.C.",
    # Rule 3: Apostrophes (APOS_SECOND)
    "o'reilly", "l'grange", "d'angelo", "o'connell", "l'enfant", "o'grange's",
    "O'Reilly", "l'Grange", "D'Angelo", "o'melveny", "o'doyle",
    # Rule 4: Scottish / Irish prefixes (MAC_MC)
    "mcdonalds", "mactavish", "mcclelland", "mcfoo", "mcneustadt", "macdonald",
    "McTavish", "MacDonald", "mcbar", "MCFOO", "mcfoo-bar",
    # Rule 5: Honorifics (MR_MRS_MS_DR)
    "mr", "mrs", "ms", "dr", "Dr", "Mr", "Mrs", "Ms", "mr.", "mrs.", "ms.", "dr.",
    # Rule 6: Inline periods & existing uppercase
    "example.com", "del.icio.us", "iTunes", "iPhone", "OmniFocus", "AT&T", "Q&A",
    "http://example.org", "github.com", "vapo(u)rware", "LaTeX", "NodeJS",
    # Rule 7: Small words
    "a", "an", "and", "as", "at", "but", "by", "en", "for", "if", "in",
    "of", "on", "or", "the", "to", "v", "v.", "via", "vs", "vs.",
    # Rule 8: Slash-delimited
    "and/or", "word/word", "input/output", "dance/sing", "client/server", "true/false",
    # Rule 9: Hyphen-delimited
    "a-b", "end-to-end", "two-not-three", "sub-phrase", "state-of-the-art", "peer-to-peer",
    # Rule 10: All-consonants acronyms
    "cnn", "tcp", "udp", "bbc", "fbi", "nfl", "xml", "html", "rst", "txt", "cfg",
    # Punctuation & Quotes
    "'by the way'", '"a trick"', "‘a trick’", "“young and restless”"
]

SMALL_WORDS = [
    "a", "an", "and", "as", "at", "but", "by", "en", "for", "if",
    "in", "of", "on", "or", "the", "to", "v", "v.", "via", "vs", "vs."
]

NORMAL_WORDS = [
    "quick", "brown", "fox", "jumps", "over", "lazy", "dog", "running",
    "developer", "software", "engineering", "guide", "handbook", "tutorial",
    "systems", "programming", "language", "design", "architecture", "patterns",
    "distributed", "computing", "database", "query", "optimization", "performance",
    "cloud", "native", "security", "protocols", "network", "packet", "stream",
    "introduction", "advanced", "fundamentals", "principles", "techniques",
    "analysis", "algorithms", "data", "structures", "practice", "theory",
    "learning", "machine", "deep", "neural", "models", "intelligence",
    "modern", "effective", "practical", "mastering", "complete", "definitive",
    "journey", "chronicles", "adventures", "tales", "stories", "history",
    "future", "world", "universe", "galaxy", "science", "nature", "space",
    "time", "quantum", "digital", "analog", "signal", "process", "memory",
    "compiler", "interpreter", "runtime", "garbage", "collection", "concurrency",
    "parallelism", "asynchronous", "synchronous", "reactive", "functional",
    "object", "oriented", "declarative", "imperative", "syntax", "semantics",
    "verification", "testing", "benchmarks", "evaluation", "frameworks", "tools"
]

SUBPHRASE_DELIMS = [
    ": ", "; ", ". ", "? ", "! ", " - ", " — ", " – "
]


def generate_single_title():
    """Generate one title mixing normal words, small words, and tricky cases."""
    pattern_type = random.randint(1, 10)

    if pattern_type == 1:
        # All-caps line with initials and tricky words (Rule 2)
        num_words = random.randint(2, 6)
        parts = []
        for _ in range(num_words):
            r = random.random()
            if r < 0.3:
                parts.append(random.choice(["D.C.", "A.B.", "U.S.", "CNN", "TCP", "AT&T", "Q&A"]))
            elif r < 0.55:
                parts.append(random.choice(SMALL_WORDS).upper())
            else:
                parts.append(random.choice(NORMAL_WORDS).upper())
        return " ".join(parts)

    elif pattern_type == 2:
        # Subphrase with punctuation followed by small word or tricky case (Rule 14)
        left = generate_phrase(random.randint(1, 4))
        delim = random.choice(SUBPHRASE_DELIMS)
        small_start = random.choice(SMALL_WORDS)
        if random.random() < 0.3:
            q = random.choice(["'", '"', "‘", "“"])
            q_close = "'" if q == "'" else ('"' if q == '"' else ('’' if q == '‘' else '”'))
            right = f"{q}{small_start} {generate_phrase(random.randint(1, 3))}{q_close}"
        else:
            right = f"{small_start} {generate_phrase(random.randint(1, 4))}"
        return f"{left}{delim}{right}"

    elif pattern_type == 3:
        # Title starting with small word (Rule 12)
        small = random.choice(SMALL_WORDS)
        rest = generate_phrase(random.randint(2, 5))
        if random.random() < 0.3:
            q = random.choice(["'", '"', "‘", "“"])
            q_close = "'" if q == "'" else ('"' if q == '"' else ('’' if q == '‘' else '”'))
            return f"{q}{small}{q_close} {rest}"
        return f"{small} {rest}"

    elif pattern_type == 4:
        # Title ending with small word (Rule 13)
        start = generate_phrase(random.randint(2, 5))
        small = random.choice(SMALL_WORDS)
        punct = random.choice(["", ".", "?", "!", '?"', ".'", "!'"])
        return f"{start} {small}{punct}"

    elif pattern_type == 5:
        # Heavy tricky elements (Mc, O', honorifics, slashes, hyphens)
        num_items = random.randint(3, 7)
        items = []
        for _ in range(num_items):
            r = random.random()
            if r < 0.45:
                items.append(random.choice(NOTES_TRICKY_CASES))
            elif r < 0.7:
                items.append(random.choice(SMALL_WORDS))
            else:
                items.append(random.choice(NORMAL_WORDS))
        return " ".join(items)

    elif pattern_type == 6:
        # Slash and hyphen compounds (Rules 8 and 9)
        w1 = random.choice([random.choice(NORMAL_WORDS), random.choice(NOTES_TRICKY_CASES), random.choice(SMALL_WORDS)])
        w2 = random.choice([random.choice(NORMAL_WORDS), random.choice(NOTES_TRICKY_CASES), random.choice(SMALL_WORDS)])
        compound = f"{w1}/{w2}" if random.random() < 0.5 else f"{w1}-{w2}"
        surrounding_left = generate_phrase(random.randint(1, 3))
        surrounding_right = generate_phrase(random.randint(1, 3))
        return f"{surrounding_left} {compound} {surrounding_right}"

    elif pattern_type == 7:
        # Apostrophe second letter (Rule 3)
        apo = random.choice(["o'reilly", "l'grange", "d'angelo", "o'connell", "o'neil", "l'enfant"])
        if random.random() < 0.3:
            apo = apo.upper()
        elif random.random() < 0.3:
            apo = apo.capitalize()
        before = generate_phrase(random.randint(1, 3))
        after = generate_phrase(random.randint(1, 3))
        return f"{before} {apo} {after}"

    elif pattern_type == 8:
        # Acronyms with all consonants or mixed-case brand names (Rules 6 & 10)
        special = random.choice(["cnn", "tcp", "udp", "bbc", "xml", "html", "iTunes", "iPhone", "example.com", "del.icio.us", "AT&T"])
        before = generate_phrase(random.randint(1, 3))
        after = generate_phrase(random.randint(1, 3))
        return f"{before} {special} {after}"

    elif pattern_type == 9:
        # Lowercase sentence with small words (Rule 7)
        words = []
        for _ in range(random.randint(4, 9)):
            if random.random() < 0.4:
                words.append(random.choice(SMALL_WORDS))
            else:
                words.append(random.choice(NORMAL_WORDS))
        return " ".join(words)

    else:
        # General mixed title (Rules 4, 5, 11)
        num_words = random.randint(3, 8)
        words = []
        for _ in range(num_words):
            choice_pool = random.random()
            if choice_pool < 0.35:
                words.append(random.choice(NOTES_TRICKY_CASES))
            elif choice_pool < 0.6:
                words.append(random.choice(SMALL_WORDS))
            else:
                w = random.choice(NORMAL_WORDS)
                if random.random() < 0.2:
                    w = w.upper()
                words.append(w)
        return " ".join(words)


def generate_phrase(length):
    """Helper to generate a short phrase of length words."""
    words = []
    for _ in range(max(1, length)):
        r = random.random()
        if r < 0.25:
            words.append(random.choice(SMALL_WORDS))
        elif r < 0.5:
            words.append(random.choice(NOTES_TRICKY_CASES))
        else:
            w = random.choice(NORMAL_WORDS)
            if random.random() < 0.15:
                w = w.upper()
            words.append(w)
    return " ".join(words)


def generate_dataset(count):
    """Generate `count` unique titles."""
    titles = []
    seen = set()
    while len(titles) < count:
        t = generate_single_title().strip()
        t = " ".join(t.split())
        if t and t not in seen:
            seen.add(t)
            titles.append(t)
    return titles


def main():
    random.seed(1)

    data_dir = SCRIPT_DIR / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    inputs_path = data_dir / "inputs.txt"
    expected_path = data_dir / "expected.txt"
    hidden_inputs_path = data_dir / "hidden_inputs.txt"
    hidden_expected_path = data_dir / "hidden_expected.txt"

    print("Generating 2000 titles into tests/data/inputs.txt...")
    inputs = generate_dataset(2000)

    print("Generating 2000 different titles into tests/data/hidden_inputs.txt...")
    hidden_inputs = generate_dataset(2000)

    print("Running original titlecase() on inputs.txt...")
    expected = [titlecase(line) for line in inputs]

    print("Running original titlecase() on hidden_inputs.txt...")
    hidden_expected = [titlecase(line) for line in hidden_inputs]

    print(f"Writing {inputs_path}...")
    with open(inputs_path, "w", encoding="utf-8") as f:
        for line in inputs:
            f.write(f"{line}\n")

    print(f"Writing {expected_path}...")
    with open(expected_path, "w", encoding="utf-8") as f:
        for line in expected:
            f.write(f"{line}\n")

    print(f"Writing {hidden_inputs_path}...")
    with open(hidden_inputs_path, "w", encoding="utf-8") as f:
        for line in hidden_inputs:
            f.write(f"{line}\n")

    print(f"Writing {hidden_expected_path}...")
    with open(hidden_expected_path, "w", encoding="utf-8") as f:
        for line in hidden_expected:
            f.write(f"{line}\n")

    print("Done! All 4 files generated with 2000 lines each.")


if __name__ == "__main__":
    main()

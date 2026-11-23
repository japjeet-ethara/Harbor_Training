#!/usr/bin/env python3
import os
import random
import sys
from pathlib import Path

# Ensure python-titlecase is importable
repo_root = Path(__file__).resolve().parent.parent
candidates = [
    repo_root / "environment" / "python-titlecase",
    repo_root.parent / "python-titlecase",
]
for c in candidates:
    if (c / "titlecase").is_dir():
        sys.path.insert(0, str(c))
        break

from titlecase import titlecase, tests

def get_base_samples():
    samples = []
    # Extract test strings from upstream tests.py TEST_DATA
    for item in tests.TEST_DATA:
        if isinstance(item, (list, tuple)) and len(item) >= 2:
            inp = item[0]
            # Replace internal newlines so each title is strictly one line
            cleaned = inp.replace("\r", " ").replace("\n", " ")
            samples.append(cleaned)
    return samples

SMALL_WORDS = ["a", "an", "and", "as", "at", "but", "by", "en", "for", "if", "in", "of", "on", "or", "the", "to", "v", "v.", "via", "vs", "vs."]
NORMAL_WORDS = [
    "lord", "rings", "tale", "cities", "war", "peace", "guide", "galaxy", "great", "expectations",
    "brave", "new", "world", "catcher", "rye", "sound", "fury", "sun", "also", "rises", "grapes", "wrath",
    "pride", "prejudice", "sense", "sensibility", "crime", "punishment", "brothers", "karamazov",
    "odyssey", "iliad", "republic", "prince", "art", "zen", "motorcycle", "maintenance"
]
ACRONYMS = ["CNN", "BBC", "FBI", "CIA", "NASA", "HTML", "XML", "CSS", "JSON", "AT&T", "Q&A", "SEC", "IBM", "AMD"]
CONSONANTS = ["cnn", "bbc", "fbi", "fwd", "ctrl", "alt", "del", "psst", "rhythm", "lynx", "sync"]
SPECIAL_FORMS = [
    "dr", "mr", "mrs", "ms", "dr.", "mr.", "mrs.", "ms.", "mcdonald", "macdonald", "mcintosh", "mclaren",
    "o'reilly", "d'angelo", "l'enfant", "o'clock", "don't", "can't", "won't", "it's", "that's",
    "u.s.", "u.s.a.", "d.c.", "e.u.", "example.com", "del.icio.us", "node.js", "python.org",
    "mother-in-law", "state-of-the-art", "end-to-end", "step-by-step", "part-time",
    "input/output", "and/or", "client/server", "tcp/ip", "yes/no", "on/off"
]
PUNCT_PREFIXES = ["'", '"', '‘', '“', '(', '[', '{', '¿', '¡']
PUNCT_SUFFIXES = ["'", '"', '’', '”', ')', ']', '}', '?', '!', '.', ':', ';']
SUBPHRASE_DELIMS = [": ", "; ", ". ", "? ", "! ", " - ", " — ", " – "]

def make_random_title(rng):
    choice = rng.random()
    if choice < 0.2:
        # Punctuation / subphrase edge case
        p1 = rng.choice(NORMAL_WORDS + SPECIAL_FORMS + ACRONYMS)
        delim = rng.choice(SUBPHRASE_DELIMS)
        sw = rng.choice(SMALL_WORDS)
        p2 = rng.choice(NORMAL_WORDS + SPECIAL_FORMS)
        quote = rng.choice(["", "'", '"', '‘', '“'])
        if quote:
            closing = "'" if quote in ("'", '‘') else '"'
            return f"{p1}{delim}{quote}{sw} {p2}{closing}"
        return f"{p1}{delim}{sw} {p2}"
    elif choice < 0.35:
        # Hyphenated / slashed composite
        p1 = rng.choice(SPECIAL_FORMS + NORMAL_WORDS)
        op = rng.choice(["-", "/"])
        p2 = rng.choice(SMALL_WORDS)
        p3 = rng.choice(NORMAL_WORDS)
        return f"{p1}{op}{p2}{op}{p3}"
    elif choice < 0.5:
        # All-caps or all-consonant line
        words = [rng.choice(NORMAL_WORDS + SMALL_WORDS + CONSONANTS) for _ in range(rng.randint(2, 6))]
        line = " ".join(words)
        return line.upper() if rng.random() < 0.7 else line
    elif choice < 0.65:
        # Initials, honorifics, apostrophes
        words = [rng.choice(SPECIAL_FORMS) for _ in range(rng.randint(1, 3))]
        words.extend([rng.choice(NORMAL_WORDS) for _ in range(rng.randint(1, 3))])
        rng.shuffle(words)
        return " ".join(words)
    elif choice < 0.8:
        # Unusual whitespace or punctuation wrappers
        words = [rng.choice(NORMAL_WORDS + SMALL_WORDS) for _ in range(rng.randint(2, 5))]
        sep = "   " if rng.random() < 0.5 else "  "
        line = sep.join(words)
        if rng.random() < 0.4:
            line = f"{rng.choice(PUNCT_PREFIXES)}{line}{rng.choice(PUNCT_SUFFIXES)}"
        return line
    else:
        # Standard sentence with leading / trailing small words
        words = [rng.choice(SMALL_WORDS)]
        words.extend([rng.choice(NORMAL_WORDS + SMALL_WORDS) for _ in range(rng.randint(2, 5))])
        words.append(rng.choice(SMALL_WORDS))
        return " ".join(words)

def generate_dataset(seed, count, base_samples, rng):
    titles = []
    # Always include the exact upstream test cases
    for s in base_samples:
        titles.append(s)
    
    # Fill up to count with deterministic variations
    while len(titles) < count:
        titles.append(make_random_title(rng))
        
    return titles[:count]

def main():
    data_dir = repo_root / "tests" / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # Deterministic generation
    rng = random.Random(1)
    base_samples = get_base_samples()
    
    visible_titles = generate_dataset(seed=1, count=2000, base_samples=base_samples, rng=rng)
    
    # Hidden dataset (different sample generation)
    hidden_titles = []
    # Add an empty line edge case to hidden
    hidden_titles.append("")
    while len(hidden_titles) < 2000:
        hidden_titles.append(make_random_title(rng))
    
    # Compute expected outputs using upstream python titlecase
    print(f"Generating 2000 visible titles...")
    visible_expected = [titlecase(t) for t in visible_titles]
    
    print(f"Generating 2000 hidden titles...")
    hidden_expected = [titlecase(t) for t in hidden_titles]
    
    # Write files
    (data_dir / "inputs.txt").write_text("\n".join(visible_titles) + "\n", encoding="utf-8")
    (data_dir / "expected.txt").write_text("\n".join(visible_expected) + "\n", encoding="utf-8")
    (data_dir / "hidden_inputs.txt").write_text("\n".join(hidden_titles) + "\n", encoding="utf-8")
    (data_dir / "hidden_expected.txt").write_text("\n".join(hidden_expected) + "\n", encoding="utf-8")
    
    print(f"Done! Written datasets to {data_dir}")

if __name__ == "__main__":
    main()

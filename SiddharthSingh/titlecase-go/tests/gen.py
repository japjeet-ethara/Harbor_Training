#!/usr/bin/env python3
"""
Test input and expected output generator for titlecase Harbor benchmark.
Generates 2,000 visible titles and 2,000 hidden titles with deterministic pseudo-random seeds.
Runs the original python-titlecase implementation on every line to freeze expected answers.
"""

import os
import random
import sys

# Add python-titlecase to Python path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..", "..", "python-titlecase"))
if not os.path.exists(os.path.join(REPO_ROOT, "titlecase")):
    # Try alternate location inside environment
    ALT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..", "environment", "python-titlecase"))
    if os.path.exists(os.path.join(ALT_ROOT, "titlecase")):
        REPO_ROOT = ALT_ROOT

sys.path.insert(0, REPO_ROOT)
from titlecase import titlecase

WORDS = [
    "the", "a", "an", "and", "as", "at", "but", "by", "en", "for", "if", "in", "of", "on", "or", "to", "via", "vs", "v",
    "quick", "brown", "fox", "jumps", "over", "lazy", "dog", "report", "system", "guide", "manual",
    "apple", "google", "microsoft", "amazon", "linux", "windows", "unix", "kernel", "server", "network",
    "development", "architecture", "design", "specification", "analysis", "security", "framework",
    "algorithm", "performance", "database", "query", "storage", "memory", "function", "variable",
    "mr", "mrs", "ms", "dr", "st", "jr", "sr",
    "mcdonald", "mctavish", "macintosh", "macarthur", "o'connor", "o'reilly", "l'enfant", "d'angelo",
    "cnn", "bbc", "fbi", "cia", "nasa", "html", "http", "json", "xml", "rest", "api", "cli",
    "del.icio.us", "example.com", "github.com", "golang.org", "file.txt", "document.pdf",
    "itunes", "ipod", "iphone", "ebay", "at&t", "q&a"
]

PUNCT_PREFIXES = ["", "\"", "'", "“", "‘", "(", "[", "{"]
PUNCT_SUFFIXES = ["", "\"", "'", "”", "’", ")", "]", "}", ",", ":", ";", "!", "?"]
SUBPHRASE_SEPARATORS = [": ", "; ", "- ", " – ", " — ", "? ", "! ", ". "]

def generate_title(rng):
    mode = rng.randint(1, 10)
    
    # Mode 1: Small word at start/end
    if mode == 1:
        start_small = rng.choice(["a", "an", "the", "in", "of", "to", "for", "on"])
        middle = [rng.choice(WORDS) for _ in range(rng.randint(2, 5))]
        end_small = rng.choice(["in", "of", "to", "for", "on", "by", "at", "as"])
        return f"{start_small} {' '.join(middle)} {end_small}"
    
    # Mode 2: Subphrase with separator
    elif mode == 2:
        part1 = " ".join([rng.choice(WORDS) for _ in range(rng.randint(2, 4))])
        sep = rng.choice(SUBPHRASE_SEPARATORS)
        small = rng.choice(["a", "an", "the", "and", "or", "in", "on", "of", "to"])
        part2 = " ".join([rng.choice(WORDS) for _ in range(rng.randint(2, 4))])
        quote = rng.choice(["", "'", "\""])
        return f"{part1}{sep}{quote}{small} {part2}{quote}".strip()
    
    # Mode 3: Slash / hyphen compounds
    elif mode == 3:
        w1 = rng.choice(WORDS)
        w2 = rng.choice(["and/or", "dance/music", "end-to-end", "step-by-step", "two-not-three", "three-by-four", "o'melveny/o'doyle"])
        w3 = rng.choice(WORDS)
        return f"{w1} {w2} {w3}"
    
    # Mode 4: All-caps sentence or initials
    elif mode == 4:
        submode = rng.choice([1, 2])
        if submode == 1:
            words = [rng.choice(WORDS) for _ in range(rng.randint(3, 6))]
            return " ".join(words).upper()
        else:
            initial = rng.choice(["WASHINGTON, D.C.", "U.S.A.", "N.Y.C.", "E.U."])
            rest = " ".join([rng.choice(WORDS) for _ in range(rng.randint(3, 5))])
            return f"{initial} {rest.upper()}"
    
    # Mode 5: Consonant acronyms
    elif mode == 5:
        acronym = rng.choice(["cnn", "bbc", "fbi", "cia", "nasa", "html", "xml", "json", "cli", "tst"])
        words = [rng.choice(WORDS) for _ in range(rng.randint(3, 6))]
        pos = rng.randint(0, len(words))
        words.insert(pos, acronym)
        return " ".join(words)
    
    # Mode 6: Irish / Scottish / Romance prefixes (Mc, Mac, O', l', d')
    elif mode == 6:
        name = rng.choice([
            "mcdonald", "mctavish", "macdonald", "macarthur",
            "o'reilly", "o'neill", "o'connor", "o'brien", "o'grange's",
            "l'grange", "l'enfant", "d'angelo", "d'artagnan"
        ])
        title = rng.choice(["mr", "mrs", "ms", "dr", ""])
        words = [rng.choice(WORDS) for _ in range(rng.randint(2, 5))]
        prefix = f"{title} {name}".strip()
        return f"{prefix} {' '.join(words)}"
    
    # Mode 7: Technical tokens (domain names, file extensions, interior caps)
    elif mode == 7:
        tech = rng.choice(["del.icio.us", "example.com", "github.com", "golang.org", "iTunes", "iPod", "iPhone", "AT&T", "eBay", "Q&A"])
        words = [rng.choice(WORDS) for _ in range(rng.randint(3, 6))]
        pos = rng.randint(0, len(words))
        words.insert(pos, tech)
        return " ".join(words)
    
    # Mode 8: Quoted and parenthesized tokens
    elif mode == 8:
        p_pre = rng.choice(PUNCT_PREFIXES)
        p_suf = rng.choice(PUNCT_SUFFIXES)
        small = rng.choice(["by the way", "a thing", "in the know", "nothing to be afraid of"])
        rest = " ".join([rng.choice(WORDS) for _ in range(rng.randint(2, 4))])
        return f"{p_pre}{small}{p_suf} {rest}".strip()
    
    # Mode 9: Multiple spaces and formatting
    elif mode == 9:
        words = [rng.choice(WORDS) for _ in range(rng.randint(3, 6))]
        sep = " " * rng.randint(2, 4)
        return sep.join(words)
    
    # Mode 10: Standard mixed phrase
    else:
        words = [rng.choice(WORDS) for _ in range(rng.randint(4, 8))]
        return " ".join(words)


def generate_dataset(seed, count):
    rng = random.Random(seed)
    titles = []
    for _ in range(count):
        t = generate_title(rng)
        # Ensure single line without carriage returns / newlines
        t = t.replace("\r", " ").replace("\n", " ").strip()
        titles.append(t)
    return titles


def main():
    data_dir = os.path.join(CURRENT_DIR, "data")
    os.makedirs(data_dir, exist_ok=True)
    
    # Deterministic generation: seed 1 for visible, seed 2 for hidden
    visible_inputs = generate_dataset(seed=1, count=2000)
    hidden_inputs = generate_dataset(seed=2, count=2000)
    
    visible_expected = [titlecase(line) for line in visible_inputs]
    hidden_expected = [titlecase(line) for line in hidden_inputs]
    
    # Write inputs.txt
    with open(os.path.join(data_dir, "inputs.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(visible_inputs) + "\n")
        
    # Write expected.txt
    with open(os.path.join(data_dir, "expected.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(visible_expected) + "\n")
        
    # Write hidden_inputs.txt
    with open(os.path.join(data_dir, "hidden_inputs.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(hidden_inputs) + "\n")
        
    # Write hidden_expected.txt
    with open(os.path.join(data_dir, "hidden_expected.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(hidden_expected) + "\n")
        
    print(f"Generated 2000 visible lines in {os.path.join(data_dir, 'inputs.txt')}")
    print(f"Generated 2000 visible answers in {os.path.join(data_dir, 'expected.txt')}")
    print(f"Generated 2000 hidden lines in {os.path.join(data_dir, 'hidden_inputs.txt')}")
    print(f"Generated 2000 hidden answers in {os.path.join(data_dir, 'hidden_expected.txt')}")

if __name__ == "__main__":
    main()


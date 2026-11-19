#!/usr/bin/env python3
"""
Generate test inputs and freeze expected outputs using the original Python titlecase.
Run from the titlecase-go directory:
    python tests/gen.py
"""

import os
import sys
import random

# Add the python-titlecase repo to path so we can import it
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'environment', 'python-titlecase'))
from titlecase import titlecase

random.seed(1)

# ─── word pools ───
NORMAL_WORDS = [
    "hello", "world", "python", "programming", "language", "computer", "science",
    "algorithm", "function", "variable", "class", "object", "method", "library",
    "framework", "database", "network", "server", "client", "application",
    "development", "software", "engineer", "design", "pattern", "structure",
    "interface", "module", "package", "system", "process", "thread", "memory",
    "storage", "cache", "queue", "stack", "tree", "graph", "table", "index",
    "search", "sort", "filter", "transform", "render", "compile", "execute",
    "deploy", "monitor", "debug", "test", "build", "release", "version",
    "update", "patch", "feature", "bug", "fix", "issue", "request", "response",
    "data", "stream", "buffer", "channel", "signal", "event", "handler",
    "listener", "observer", "factory", "builder", "adapter", "proxy", "bridge",
    "strategy", "command", "state", "template", "visitor", "iterator",
    "singleton", "prototype", "decorator", "facade", "composite", "flyweight",
    "mediator", "memento", "chain", "interpreter", "responsibility",
    "beautiful", "morning", "sunset", "ocean", "mountain", "river", "forest",
    "garden", "flower", "animal", "bird", "fish", "star", "moon", "planet",
    "galaxy", "universe", "music", "painting", "sculpture", "dance", "theater",
    "novel", "poem", "story", "chapter", "paragraph", "sentence", "word",
    "letter", "number", "equation", "formula", "theorem", "proof", "hypothesis",
    "experiment", "observation", "conclusion", "discovery", "invention",
    "innovation", "revolution", "evolution", "civilization", "culture",
    "tradition", "heritage", "legacy", "wisdom", "knowledge", "education",
]

SMALL_WORDS = [
    "a", "an", "and", "as", "at", "but", "by", "en", "for", "if", "in",
    "of", "on", "or", "the", "to", "v.", "via", "vs.", "v", "vs",
]

TRICKY_INPUTS = [
    # Apostrophe-second words
    "o'brien's journey to the west",
    "d'artagnan and the musketeers",
    "l'oreal paris new collection",
    # Mc/Mac names
    "mcdonald's franchise in mckinney",
    "macarthur park is melting",
    "mccarthy and the senate",
    # Mixed case / camelCase
    "the iPhone revolution by apple",
    "eBay and PayPal partnership",
    "testing jQuery and AngularJS",
    # Inline periods
    "the u.s.a. government report",
    "dr. smith and prof. jones",
    "e.g. this is an example i.e. here",
    # ALL CAPS
    "THE LORD OF THE RINGS",
    "NASA ANNOUNCES NEW MISSION",
    "FBI AND CIA JOINT OPERATION",
    # UC Initials
    "A.B.C. NEWS REPORT",
    "J.R.R. TOLKIEN BIOGRAPHY",
    # Hyphenated
    "the self-aware robot uprising",
    "well-known facts about the mid-atlantic",
    "twenty-first century of innovation",
    "state-of-the-art technology in AI",
    # Slash-separated (not URLs)
    "work/life balance and AC/DC concert",
    "input/output devices for the lab",
    # URLs (should be preserved)
    "visit https://example.com for more",
    "check http://docs.go.dev/tutorial today",
    # Subphrase punctuation
    "a tale: the beginning of the end",
    "question? the answer is clear",
    "warning! the bridge is out",
    "first part; the second follows",
    "start here - the rest is easy",
    # Small words at start/end
    "the the",
    "nothing to be afraid of",
    "of mice and men",
    "a story of the time",
    "to be or not to be",
    # Mr/Mrs/Ms/Dr
    "mr smith and mrs jones attend",
    "ms taylor and dr williams present",
    # All consonants (acronyms)
    "the nfl draft picks",
    "nbc news and cbs reports",
    "the bbc world service",
    # Edge cases
    "",
    "a",
    "THE",
    "42",
    "hello",
    "hello world",
    "  leading spaces preserved",
    # Punctuation at start
    "\"hello world\" by the author",
    "(the beginning) of time",
    "[important] the final chapter",
    # Em-dash / en-dash subphrase
    "the plan — the execution",
    "phase one – the overview",
    # vs. and v.
    "smith vs. jones in court",
    "roe v. wade revisited",
    # Multiple spaces (should be preserved)
    "hello   world   test",
    # Mixed tricky combinations
    "o'brien's mcdonald's on the iPhone via eBay",
    "THE STATE-OF-THE-ART NFL A.B.C. REPORT",
    "dr. mccarthy's well-known d'artagnan theory: the proof",
]

def generate_random_title(rng):
    """Generate one random title mixing normal and tricky words."""
    length = rng.randint(3, 12)
    words = []
    for _ in range(length):
        r = rng.random()
        if r < 0.15:
            words.append(rng.choice(SMALL_WORDS))
        elif r < 0.20:
            # All caps word
            words.append(rng.choice(NORMAL_WORDS).upper())
        elif r < 0.25:
            # hyphenated
            w1 = rng.choice(NORMAL_WORDS)
            w2 = rng.choice(NORMAL_WORDS)
            words.append(f"{w1}-{w2}")
        elif r < 0.28:
            # slash separated
            w1 = rng.choice(NORMAL_WORDS)
            w2 = rng.choice(NORMAL_WORDS)
            words.append(f"{w1}/{w2}")
        elif r < 0.30:
            # Mc/Mac name
            words.append("mc" + rng.choice(NORMAL_WORDS))
        else:
            words.append(rng.choice(NORMAL_WORDS))
    
    # Sometimes make it all caps
    title = " ".join(words)
    if rng.random() < 0.08:
        title = title.upper()
    return title


def generate_inputs(count, rng):
    """Generate `count` inputs, mixing random titles with tricky ones."""
    inputs = []
    # Sprinkle in tricky inputs
    tricky_count = min(len(TRICKY_INPUTS), count // 10)
    tricky_indices = set(rng.sample(range(count), tricky_count))
    tricky_iter = iter(TRICKY_INPUTS[:tricky_count])
    
    for i in range(count):
        if i in tricky_indices:
            inputs.append(next(tricky_iter))
        else:
            inputs.append(generate_random_title(rng))
    return inputs


def main():
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    os.makedirs(data_dir, exist_ok=True)

    rng = random.Random(1)

    # Generate visible inputs (2000 lines)
    visible_inputs = generate_inputs(2000, rng)
    
    # Generate hidden inputs (2000 lines) with a different portion of the random stream
    hidden_inputs = generate_inputs(2000, rng)

    # Freeze expected outputs using the ORIGINAL Python titlecase
    visible_expected = [titlecase(line) for line in visible_inputs]
    hidden_expected = [titlecase(line) for line in hidden_inputs]

    # Write all four files
    with open(os.path.join(data_dir, "inputs.txt"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(visible_inputs) + "\n")

    with open(os.path.join(data_dir, "expected.txt"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(visible_expected) + "\n")

    with open(os.path.join(data_dir, "hidden_inputs.txt"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(hidden_inputs) + "\n")

    with open(os.path.join(data_dir, "hidden_expected.txt"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(hidden_expected) + "\n")

    # Print summary
    for name in ["inputs.txt", "expected.txt", "hidden_inputs.txt", "hidden_expected.txt"]:
        path = os.path.join(data_dir, name)
        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        print(f"{name}: {len(lines)} lines")


if __name__ == "__main__":
    main()

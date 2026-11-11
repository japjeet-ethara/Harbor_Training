#!/usr/bin/env python3
"""
Generate visible and hidden test datasets for titlecase-go.
Uses random.seed(1) for deterministic output.
Runs the original Python titlecase implementation to generate expected answers.
"""

import os
import random
import sys

# Add python-titlecase to path
REPO_PATHS = [
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../../python-titlecase")),
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../environment/repo")),
]
for p in REPO_PATHS:
    if os.path.exists(os.path.join(p, "titlecase", "__init__.py")):
        sys.path.insert(0, p)
        break

from titlecase import titlecase

# Word pools for generating synthetic titles
NORMAL_NOUNS = [
    "dog", "cat", "bird", "mountain", "river", "ocean", "valley", "forest",
    "king", "queen", "prince", "princess", "warrior", "wizard", "journey",
    "chronicles", "odyssey", "history", "guide", "handbook", "story", "tale",
    "legend", "mystery", "secret", "shadow", "light", "darkness", "dragon",
    "empire", "republic", "station", "system", "network", "computer", "engine",
    "algorithm", "theory", "practice", "method", "principle", "standard"
]

NORMAL_ADJECTIVES = [
    "great", "small", "ancient", "modern", "brave", "silent", "lost", "found",
    "hidden", "forgotten", "golden", "silver", "iron", "dark", "bright",
    "wild", "calm", "rough", "smooth", "deep", "high", "true", "false",
    "final", "first", "last", "new", "old", "young", "eternal", "infinite"
]

NORMAL_VERBS = [
    "runs", "walks", "flies", "swims", "climbs", "falls", "rises", "speaks",
    "whispers", "shouts", "listens", "watches", "waits", "knows", "thinks",
    "believes", "fights", "wins", "loses", "discovers", "builds", "destroys"
]

SMALL_WORDS = [
    "a", "an", "and", "as", "at", "but", "by", "en", "for", "if",
    "in", "of", "on", "or", "the", "to", "v", "v.", "via", "vs", "vs."
]

ACRONYMS_CONSONANTS = [
    "cnn", "tcp", "udp", "xml", "html", "sql", "dns", "mss", "bgp", "smtp",
    "cpu", "fbi", "cia", "ibm", "bbc", "npr", "tnt", "kfc", "dvd", "gps"
]

ACRONYMS_INITIALS = [
    "D.C.", "A.B.", "U.S.A.", "Ph.D.", "e.g.", "i.e.", "N.Y.C.", "W.H.O."
]

BRAND_NAMES = [
    "iTunes", "iPhone", "iPad", "eBay", "AT&T", "OmniFocus", "MacDonalds",
    "PlayStation", "YouTube", "JavaScript", "PostgreSQL", "GitHub"
]

MC_NAMES = [
    "mcdonalds", "mctavish", "mccay", "mcbut", "mcdo", "mcby", "mcfoo",
    "mcbar", "mcneustadt", "mcclelland", "mcmaier", "machine", "mac"
]

APOS_NAMES = [
    "o'reilly", "o'grange", "o'connor", "o'melveny", "o'doyle",
    "l'grange", "l'enfant", "l'hospital", "L'grange",
    "d'angelo", "d'artagnan", "d'amato", "d'angelo's"
]

HONORIFICS = [
    "mr", "mr.", "mrs", "mrs.", "ms", "ms.", "dr", "dr.",
    "Mr", "Mr.", "Mrs", "Mrs.", "Ms", "Ms.", "Dr", "Dr.", "DR", "MRS"
]

ORDINALS = [
    "1st", "2nd", "3rd", "4th", "5th", "10th", "21st", "34th", "100th"
]

SLASH_COMPOUNDS = [
    "and/or", "either/or", "input/output", "read/write", "client/server",
    "two/three", "yes/no", "true/false", "before/after", "stop/start",
    "three-by-four/five-and", "mcdonalds/mcby"
]

HYPHEN_COMPOUNDS = [
    "end-to-end", "a-b", "two-not-three", "three-by-four", "five-and",
    "state-of-the-art", "day-to-day", "face-to-face", "step-by-step",
    "mcfoo-bar", "MCFOO-BAR", "McFoo-bar", "foo-mcbar", "up-to-date"
]

SUBPHRASE_PUNCT = [":", ";", ".", "!", "?", "-", "–", "—", "―"]

DOMAINS = [
    "example.com", "del.icio.us", "foo.org", "github.com", "golang.org",
    "python.org", "w3.org", "http://foo.com", "https://bar.org/test"
]

UNICODE_PHRASES = [
    "El Niño a Arrivé Hier", "EL NIÑO A ARRIVÉ HIER", "Crème brûlée",
    "CRÈME BRÛLÉE", "vis-à-vis", "über den wolken", "ÜBER DEN WOLKEN",
    "ÝÆ ÑØ", "ýæ ñø", "the case of X ≤ 7", "THE CASE OF X ≤ 7"
]

QUOTES = [
    ("'", "'"), ('"', '"'), ("‘", "’"), ("“", "”")
]


def generate_single_title():
    """Generates a single synthetic title exercising various rules."""
    choice = random.randint(1, 15)

    if choice == 1:
        # Standard title: [Small] [Adj] [Noun] [Small] [Noun]
        words = []
        if random.random() < 0.6:
            words.append(random.choice(SMALL_WORDS))
        words.append(random.choice(NORMAL_ADJECTIVES))
        words.append(random.choice(NORMAL_NOUNS))
        if random.random() < 0.7:
            words.append(random.choice(SMALL_WORDS))
            words.append(random.choice(NORMAL_NOUNS))
        return " ".join(words)

    elif choice == 2:
        # All caps title
        words = [
            random.choice(NORMAL_NOUNS),
            random.choice(SMALL_WORDS),
            random.choice(NORMAL_ADJECTIVES),
            random.choice(NORMAL_NOUNS)
        ]
        if random.random() < 0.4:
            words.append(random.choice(ACRONYMS_INITIALS))
        return " ".join(words).upper()

    elif choice == 3:
        # Title with Mc / Mac
        mc = random.choice(MC_NAMES)
        if random.random() < 0.3:
            mc = mc.upper()
        noun = random.choice(NORMAL_NOUNS)
        verb = random.choice(NORMAL_VERBS)
        return f"{random.choice(HONORIFICS)} {mc} {verb} {random.choice(SMALL_WORDS)} {noun}"

    elif choice == 4:
        # Title with apostrophe name (d', l', o')
        apos = random.choice(APOS_NAMES)
        if random.random() < 0.2:
            apos = apos.upper()
        return f"the life of {apos} and {random.choice(APOS_NAMES)}"

    elif choice == 5:
        # Subphrase with delimiter + space + small word
        punct = random.choice(SUBPHRASE_PUNCT)
        first_part = f"{random.choice(NORMAL_ADJECTIVES)} {random.choice(NORMAL_NOUNS)}"
        small = random.choice(SMALL_WORDS)
        second_part = f"{random.choice(NORMAL_ADJECTIVES)} {random.choice(NORMAL_NOUNS)}"
        if random.random() < 0.3:
            # Quote inside subphrase
            q_open, q_close = random.choice(QUOTES)
            return f"{first_part}{punct} {q_open}{small} {second_part}{q_close}"
        return f"{first_part}{punct} {small} {second_part}"

    elif choice == 6:
        # Slashes and hyphens compounds
        compound = random.choice(SLASH_COMPOUNDS + HYPHEN_COMPOUNDS)
        return f"{random.choice(SMALL_WORDS)} {compound} {random.choice(NORMAL_NOUNS)}"

    elif choice == 7:
        # Consonant acronyms & ordinals
        acronym = random.choice(ACRONYMS_CONSONANTS)
        ordinal = random.choice(ORDINALS)
        words = [
            random.choice(["words with", "guide to", "using", "overview of"]),
            acronym,
            "on the",
            ordinal,
            random.choice(["floor", "street", "st", "attempt", "edition"])
        ]
        return " ".join(words)

    elif choice == 8:
        # Quoted start and quoted end
        q_open, q_close = random.choice(QUOTES)
        small_start = random.choice(SMALL_WORDS)
        small_end = random.choice(SMALL_WORDS)
        noun = random.choice(NORMAL_NOUNS)
        return f"{q_open}{small_start} {noun}{q_close} is nothing to be afraid {small_end}"

    elif choice == 9:
        # Tech brands & inline periods / domains
        brand = random.choice(BRAND_NAMES)
        domain = random.choice(DOMAINS)
        return f"{brand} vs {domain} for {random.choice(NORMAL_NOUNS)}"

    elif choice == 10:
        # Unicode titles
        base = random.choice(UNICODE_PHRASES)
        if random.random() < 0.5:
            return base.upper()
        return base

    elif choice == 11:
        # Whitespace variations (tabs, multiple spaces, non-breaking spaces)
        sp = random.choice(["  ", "\t", "\u00a0", "   "])
        w1 = random.choice(NORMAL_NOUNS)
        w2 = random.choice(SMALL_WORDS)
        w3 = random.choice(NORMAL_NOUNS)
        return f"{w1}{sp}{w2} {w3}"

    elif choice == 12:
        # Short strings and edge cases
        edge_cases = [
            "a", "the", "in", "vs.", "v", "34th", "2nd", "st",
            "a thing", "the end", "at&t", "q&a", "o'reilly", "l'grange",
            "dr who", "mr smith", "end-to-end", "and/or", "http://foo.com"
        ]
        return random.choice(edge_cases)

    elif choice == 13:
        # Title ending in small word with punctuation
        noun = random.choice(NORMAL_NOUNS)
        small = random.choice(["of", "in", "to", "for", "by", "with", "at"])
        punct = random.choice(["?", "!", ".", "..."])
        return f"what is {noun} afraid {small}{punct}"

    elif choice == 14:
        # All caps with subphrase and acronyms
        first = f"{random.choice(NORMAL_NOUNS)} {random.choice(NORMAL_VERBS)}".upper()
        second = f"{random.choice(SMALL_WORDS)} {random.choice(ACRONYMS_CONSONANTS)} {random.choice(NORMAL_NOUNS)}".upper()
        return f"{first}: {second}"

    else:
        # Mixed compound sentence
        w1 = random.choice(NORMAL_ADJECTIVES)
        w2 = random.choice(NORMAL_NOUNS)
        w3 = random.choice(SLASH_COMPOUNDS)
        w4 = random.choice(HYPHEN_COMPOUNDS)
        return f"{w1} {w2} with {w3} and {w4}"


def generate_dataset(count):
    lines = []
    for _ in range(count):
        title = generate_single_title()
        # Clean any accidental newlines or carriage returns
        title = title.replace("\r", " ").replace("\n", " ").strip()
        if not title:
            title = "a title"
        lines.append(title)
    return lines


def main():
    random.seed(1)

    # Generate 2000 visible and 2000 hidden inputs
    visible_inputs = generate_dataset(2000)
    hidden_inputs = generate_dataset(2000)

    # Compute expected outputs using the original Python implementation
    visible_expected = [titlecase(line) for line in visible_inputs]
    hidden_expected = [titlecase(line) for line in hidden_inputs]

    # Target directory
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    os.makedirs(data_dir, exist_ok=True)

    files_and_content = [
        ("inputs.txt", visible_inputs),
        ("expected.txt", visible_expected),
        ("hidden_inputs.txt", hidden_inputs),
        ("hidden_expected.txt", hidden_expected),
    ]

    for fname, content in files_and_content:
        path = os.path.join(data_dir, fname)
        with open(path, "w", encoding="utf-8") as f:
            for line in content:
                f.write(line + "\n")
        print(f"Wrote {len(content)} lines to {path}")


if __name__ == "__main__":
    main()

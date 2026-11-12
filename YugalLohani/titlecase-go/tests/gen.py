#!/usr/bin/env python3
"""
Generate deterministic test inputs and expected outputs for the titlecase-go task.

Writes four files under tests/data/:
  inputs.txt          — 2000 visible test titles
  expected.txt        — titlecase() output for each visible title
  hidden_inputs.txt   — 2000 hidden test titles  (DIFFERENT from visible set)
  hidden_expected.txt — titlecase() output for each hidden title

Expected outputs are produced by running the ORIGINAL Python titlecase() from
../python-titlecase — never written by hand.

Determinism guarantee: random.seed(1) is set once; running this script twice
produces byte-identical files.

Usage (from the titlecase-go/ directory):
  python tests/gen.py
"""

import os
import random
import sys

# ---------------------------------------------------------------------------
# Load the ORIGINAL python-titlecase (not any installed version).
# ---------------------------------------------------------------------------
REPO = os.path.join(os.path.dirname(__file__), '..', '..', 'python-titlecase')
sys.path.insert(0, os.path.abspath(REPO))
from titlecase import titlecase  # noqa: E402

random.seed(1)

# ---------------------------------------------------------------------------
# Word pools
# ---------------------------------------------------------------------------

SMALL_WORDS = [
    'a', 'an', 'and', 'as', 'at', 'but', 'by', 'en',
    'for', 'if', 'in', 'of', 'on', 'or', 'the', 'to',
    'v', 'v.', 'via', 'vs', 'vs.',
]

NORMAL_WORDS = [
    'apple', 'banana', 'orange', 'mango', 'pear',
    'river', 'mountain', 'ocean', 'forest', 'desert',
    'castle', 'dragon', 'knight', 'sword', 'shield',
    'python', 'golang', 'ruby', 'java', 'rust',
    'garden', 'window', 'bridge', 'tower', 'harbor',
    'planet', 'comet', 'nebula', 'galaxy', 'quasar',
    'signal', 'packet', 'server', 'router', 'buffer',
    'autumn', 'winter', 'spring', 'summer', 'season',
    'freedom', 'justice', 'wisdom', 'courage', 'honor',
    'thunder', 'lightning', 'sunrise', 'sunset', 'rainbow',
]

# Tricky single-word tokens derived from the rule analysis.
# These are MIXED IN to the generated sentences, not prepended as fixed phrases.
TRICKY_TOKENS = [
    # Mac/Mc prefix — only [Mm]c|MC patterns (matches Python's MAC_MC regex)
    'mcdonald', 'mcgregor', 'mctavish',
    'mcclelland', 'mcfoo',
    # Apostrophe-second (l', o', d') — consonant-first → lowercase prefix
    "l'grange", "l'Grange",
    # Apostrophe-second — vowel-first → uppercase prefix
    "o'reilly", "o'grange", "o'Grange",
    # UC elsewhere / mixed case to preserve
    'iTunes', 'OmniFocus', 'iPhone',
    'AT&T', 'Q&A',
    # Inline period (domain-like)
    'example.com', 'del.icio.us',
    # All-consonant acronyms (length > 2)
    'cnn', 'fbi', 'php', 'xml', 'html',
    # Mr/Mrs/Ms/Dr
    'mr', 'mrs', 'ms', 'dr', 'mss',
    # Numbers / alphanumeric (not affected by consonant rule)
    '34th', '3rd', '2nd', '5th',
    # Unicode / accented
    'niño', 'arrivé',
    # Double-slash URL (preserved by inline-period rule)
    'http://foo.com',
]

# Fixed tricky phrases — only included in the VISIBLE set.
# They test known edge cases explicitly without leaking answers to the hidden set.
TRICKY_PHRASES_VISIBLE_ONLY = [
    # Sub-phrase capitalisation after punctuation
    "Starting Sub-Phrase With a Small Word: a Trick, Perhaps?",
    "generalissimo francisco franco: still dead; kieren McCarthy: still a jackass",
    "The SEC's Apple probe: what you need to know",
    # ALL CAPS
    "THIS IS ALL CAPS AND SHOULD BE ADDRESSED",
    "EPISODE 7 \u2014 THE FORCE AWAKENS",
    "WASHINGTON, D.C. SHOULD BE FIXED BUT MIGHT BE A PROBLEM",
    # Hyphenated
    "end-to-end",
    "a-b end-to-end two-not-three",
    "mcfoo-bar, MCFOO-BAR, McFoo-bar, McFoo-Bar",
    # Slash
    "word/word",
    "a title and/or string",
    "dance with me/let's face the music and dance",
    # Apostrophe-second complex
    "l'grange l'grange l'Grange l'Grange",
    "o'grange O'grange o'Grange O'Grange",
    "o'melveny/o'doyle o'Melveny/o'doyle",
    # Quotes
    "'by the Way, small word at the start but within quotes.'",
    '"Nothing to Be Afraid of?"',
    # Inline period
    "this is just an example.com",
    "this is something listed on del.icio.us",
    "this is http://foo.com",
    # iTunes / OmniFocus
    "iTunes should be unmolested",
    "2lmc Spool: 'gruber on OmniFocus and vapo(u)rware'",
    # Mr/Mrs/Dr
    "Mr McTavish went to MacDonalds",
    "Mr mr Mrs Ms Mss Dr dr , Mr. and Mrs. Person",
    # Numeric
    "34th 3rd 2nd",
    "FOO BAR 5TH ST",
    "foo bar 5th st",
    # Unicode
    "EL NI\u00d1O A ARRIV\u00c9 HIER",
    "\u00dd\u00c6 \u00d1\u00d8",
    "\u00fd\u00e6 \u00f1\u00f8",
    # Em-dash sub-phrase
    "Starting an Em Dash Delimited Sub-Phrase With a Small Word \u2014 a Trick, Perhaps?",
    "Snakes on a Plane \u2014 The TV Edit \u2014 The Famous Line",
    # En-dash
    "episode 7 \u2013 The force awakens",
    # AT&T
    "What is AT\u0026T's problem?",
    "Apple deal with AT\u0026T falls through",
    # v / vs
    "this v that",
    "this v. that",
    "this vs that",
    "this vs. that",
    # Small word at end
    "Small word at end is nothing to be afraid of",
    # Consonant acronyms
    "Words with all consonants like cnn are acronyms",
    # mac mc (mc/Mc/MC only — not mac/Mac via MAC_MC rule)
    "mac mc MAC MC machine",
    # Empty / whitespace
    "",
    "   ",
]


def _build_sentence(length: int) -> str:
    """Build a random sentence of `length` words drawn from NORMAL+SMALL+TRICKY pools."""
    words = []
    for _ in range(length):
        r = random.random()
        if r < 0.12:
            words.append(random.choice(SMALL_WORDS))
        elif r < 0.22:
            words.append(random.choice(TRICKY_TOKENS))
        else:
            words.append(random.choice(NORMAL_WORDS))
    return ' '.join(words)


def _build_one() -> str:
    """Build a single randomly-structured title."""
    r = random.random()
    length = random.randint(2, 10)
    if r < 0.30:
        return _build_sentence(length)
    elif r < 0.45:
        # Sub-phrase with colon
        part1 = _build_sentence(random.randint(2, 5))
        part2 = _build_sentence(random.randint(1, 4))
        return f'{part1}: {part2}'
    elif r < 0.55:
        # Hyphenated word at the start
        w1 = random.choice(NORMAL_WORDS + TRICKY_TOKENS)
        w2 = random.choice(NORMAL_WORDS + SMALL_WORDS)
        rest = _build_sentence(random.randint(1, 5))
        return f'{w1}-{w2} {rest}'
    elif r < 0.63:
        # Slash phrase
        w1 = random.choice(NORMAL_WORDS + SMALL_WORDS)
        w2 = random.choice(NORMAL_WORDS + SMALL_WORDS)
        rest = _build_sentence(random.randint(1, 5))
        return f'{w1}/{w2} {rest}'
    elif r < 0.73:
        # ALL CAPS version of a sentence
        return _build_sentence(length).upper()
    elif r < 0.80:
        # Em-dash sub-phrase
        part1 = _build_sentence(random.randint(2, 4))
        part2 = _build_sentence(random.randint(1, 3))
        return f'{part1} \u2014 {part2}'
    else:
        return _build_sentence(length)


def generate_titles(n: int) -> list:
    """Generate a list of n purely random titles (no fixed-phrase prefix)."""
    return [_build_one() for _ in range(n)]


def write_pair(input_path: str, expected_path: str, titles: list) -> None:
    """
    Write titles and their titlecase() outputs.
    Strips embedded newlines so line counts always match.
    """
    clean = [t.replace('\n', ' ').replace('\r', ' ') for t in titles]
    expected = [titlecase(c) for c in clean]

    assert len(clean) == len(expected), (
        f"Line count mismatch: {len(clean)} inputs vs {len(expected)} expected"
    )

    with open(input_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(clean) + '\n')

    with open(expected_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(expected) + '\n')

    print(f"  {input_path}: {len(clean)} lines")
    print(f"  {expected_path}: {len(expected)} lines")


def main():
    out_dir = os.path.join(os.path.dirname(__file__), 'data')
    os.makedirs(out_dir, exist_ok=True)

    # Generate visible set: 2000 random titles + fixed tricky phrases.
    # Tricky phrases are appended after the random portion so they don't
    # affect the RNG state consumed by the hidden set.
    print("Generating visible set (2000 titles)...")
    visible_random = generate_titles(2000 - len(TRICKY_PHRASES_VISIBLE_ONLY))
    visible_titles = visible_random + TRICKY_PHRASES_VISIBLE_ONLY
    # Shuffle so tricky phrases are distributed throughout (deterministic).
    random.shuffle(visible_titles)
    write_pair(
        os.path.join(out_dir, 'inputs.txt'),
        os.path.join(out_dir, 'expected.txt'),
        visible_titles,
    )

    # Generate hidden set: 2000 purely random titles.
    # Uses the RNG state left after the visible set, so it differs from visible.
    print("Generating hidden set (2000 titles)...")
    hidden_titles = generate_titles(2000)
    write_pair(
        os.path.join(out_dir, 'hidden_inputs.txt'),
        os.path.join(out_dir, 'hidden_expected.txt'),
        hidden_titles,
    )

    # Sanity check: the two input sets must not be identical.
    vis_path = os.path.join(out_dir, 'inputs.txt')
    hid_path = os.path.join(out_dir, 'hidden_inputs.txt')
    with open(vis_path, encoding='utf-8') as f:
        vis_lines = f.readlines()
    with open(hid_path, encoding='utf-8') as f:
        hid_lines = f.readlines()
    assert vis_lines != hid_lines, "ERROR: visible and hidden sets are identical!"
    shared = set(vis_lines) & set(hid_lines)
    print(f"Sets differ (share {len(shared)} lines out of 2000 — expected some overlap).")
    print("Done.")


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
Generates tests/data/ inside the verifier container.
Called by test.sh with PYTHONPATH=/workspace/repo so that
`from titlecase import titlecase` uses the original Python library.

Writes:
  /tests/data/inputs.txt           — 2000 visible titles
  /tests/data/expected.txt         — titlecase() output for each
  /tests/data/hidden_inputs.txt    — 2000 hidden titles (different set)
  /tests/data/hidden_expected.txt  — titlecase() output for each

Uses random.seed(1) for full determinism.
"""

import os
import random

from titlecase import titlecase  # from PYTHONPATH=/workspace/repo

random.seed(1)

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

TRICKY_TOKENS = [
    'mcdonald', 'mcgregor', 'mctavish', 'mcclelland', 'mcfoo',
    "l'grange", "l'Grange",
    "o'reilly", "o'grange", "o'Grange",
    'iTunes', 'OmniFocus', 'iPhone',
    'AT&T', 'Q&A',
    'example.com', 'del.icio.us',
    'cnn', 'fbi', 'php', 'xml', 'html',
    'mr', 'mrs', 'ms', 'dr', 'mss',
    '34th', '3rd', '2nd', '5th',
    'niño', 'arrivé',
    'http://foo.com',
]

TRICKY_PHRASES_VISIBLE_ONLY = [
    "Starting Sub-Phrase With a Small Word: a Trick, Perhaps?",
    "generalissimo francisco franco: still dead; kieren McCarthy: still a jackass",
    "The SEC's Apple probe: what you need to know",
    "THIS IS ALL CAPS AND SHOULD BE ADDRESSED",
    "EPISODE 7 \u2014 THE FORCE AWAKENS",
    "WASHINGTON, D.C. SHOULD BE FIXED BUT MIGHT BE A PROBLEM",
    "end-to-end",
    "a-b end-to-end two-not-three",
    "mcfoo-bar, MCFOO-BAR, McFoo-bar, McFoo-Bar",
    "word/word",
    "a title and/or string",
    "dance with me/let's face the music and dance",
    "l'grange l'grange l'Grange l'Grange",
    "o'grange O'grange o'Grange O'Grange",
    "o'melveny/o'doyle o'Melveny/o'doyle",
    "'by the Way, small word at the start but within quotes.'",
    '"Nothing to Be Afraid of?"',
    "this is just an example.com",
    "this is something listed on del.icio.us",
    "this is http://foo.com",
    "iTunes should be unmolested",
    "2lmc Spool: 'gruber on OmniFocus and vapo(u)rware'",
    "Mr McTavish went to MacDonalds",
    "Mr mr Mrs Ms Mss Dr dr , Mr. and Mrs. Person",
    "34th 3rd 2nd",
    "FOO BAR 5TH ST",
    "foo bar 5th st",
    "EL NI\u00d1O A ARRIV\u00c9 HIER",
    "\u00dd\u00c6 \u00d1\u00d8",
    "\u00fd\u00e6 \u00f1\u00f8",
    "Starting an Em Dash Delimited Sub-Phrase With a Small Word \u2014 a Trick, Perhaps?",
    "Snakes on a Plane \u2014 The TV Edit \u2014 The Famous Line",
    "episode 7 \u2013 The force awakens",
    "What is AT\u0026T's problem?",
    "Apple deal with AT\u0026T falls through",
    "this v that",
    "this v. that",
    "this vs that",
    "this vs. that",
    "Small word at end is nothing to be afraid of",
    "Words with all consonants like cnn are acronyms",
    "mac mc MAC MC machine",
    "",
    "   ",
]


def _build_sentence(length):
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


def _build_one():
    r = random.random()
    length = random.randint(2, 10)
    if r < 0.30:
        return _build_sentence(length)
    elif r < 0.45:
        return (_build_sentence(random.randint(2, 5)) + ': ' +
                _build_sentence(random.randint(1, 4)))
    elif r < 0.55:
        w1 = random.choice(NORMAL_WORDS + TRICKY_TOKENS)
        w2 = random.choice(NORMAL_WORDS + SMALL_WORDS)
        return f'{w1}-{w2} {_build_sentence(random.randint(1, 5))}'
    elif r < 0.63:
        w1 = random.choice(NORMAL_WORDS + SMALL_WORDS)
        w2 = random.choice(NORMAL_WORDS + SMALL_WORDS)
        return f'{w1}/{w2} {_build_sentence(random.randint(1, 5))}'
    elif r < 0.73:
        return _build_sentence(length).upper()
    elif r < 0.80:
        return (_build_sentence(random.randint(2, 4)) + ' \u2014 ' +
                _build_sentence(random.randint(1, 3)))
    else:
        return _build_sentence(length)


def generate_titles(n):
    return [_build_one() for _ in range(n)]


def write_pair(inp_path, exp_path, titles):
    clean = [t.replace('\n', ' ').replace('\r', ' ') for t in titles]
    expected = [titlecase(c) for c in clean]
    assert len(clean) == len(expected)
    with open(inp_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(clean) + '\n')
    with open(exp_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(expected) + '\n')
    print(f"  {inp_path}: {len(clean)} lines")
    print(f"  {exp_path}: {len(expected)} lines")


out_dir = '/tests/data'
os.makedirs(out_dir, exist_ok=True)

print("Generating visible set (2000 titles)...")
visible_random = generate_titles(2000 - len(TRICKY_PHRASES_VISIBLE_ONLY))
visible_titles = visible_random + TRICKY_PHRASES_VISIBLE_ONLY
random.shuffle(visible_titles)
write_pair(
    os.path.join(out_dir, 'inputs.txt'),
    os.path.join(out_dir, 'expected.txt'),
    visible_titles,
)

print("Generating hidden set (2000 titles)...")
hidden_titles = generate_titles(2000)
write_pair(
    os.path.join(out_dir, 'hidden_inputs.txt'),
    os.path.join(out_dir, 'hidden_expected.txt'),
    hidden_titles,
)
print("Done.")

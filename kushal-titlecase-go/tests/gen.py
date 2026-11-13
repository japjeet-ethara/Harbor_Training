import hashlib
import json
import random
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / 'environment/reference'))
import regex
import titlecase

WORDS = 'harbor lantern meadow compass archive ember orchard journey signal tide river window cedar velvet amber valley copper garden winter paper ocean quiet silver forest morning canyon museum planet bright island market shadow'.split()
SMALL = 'a an and as at but by en for if in of on or the to v v. via vs vs.'.split()
NAMES = ["d'angelo", "l'grange", "o'reilly", "o'grange's", "l‘granGe", "o's'", "d’angelo", 'mcthe', 'mcby', 'MCFOO-BAR', 'mc1', 'mc_x', 'macdonald', 'mr', 'MRS', 'mss']
SPECIAL = ['ß', 'İ', 'ΟΣ', 'ΟΔΥΣΣΕΎΣ', 'ᾀ', 'ﬁ', 'ǅ', 'ſ', 'K', 'éBay', 'İTunes', 'café', 'niño', '𐐀𐐨', 'a\u0301', '\u0301word', 'ⱥ', '𞤀𞤢', 'Ꭰꭰ']
SPACES = [' ', '  ', '\t', '\u00a0', '\u2003', '\u2009', '\u202f', '\u3000', '\u000b', '\u0085', '\u2028']
MARKS = [':', '.', ';', '?', '!', '-', '–', '‒', '—', '―']
TYPES = ['plain', 'small-middle', 'small-start', 'small-end', 'subphrase', 'names', 'mixed-case', 'dotted', 'initials', 'consonants', 'slash', 'hyphen', 'leading-space', 'trailing-space', 'unicode-space', 'unicode-case', 'combining', 'punctuation', 'digit-prefix', 'recursive']


def word():
    return random.choice(WORDS)


def make(kind):
    left, right, small = word(), word(), random.choice(SMALL)
    if kind == 'plain':
        return ' '.join(word() for _ in range(random.randint(3, 8)))
    if kind == 'small-middle':
        return f'{left} {small} {right}'
    if kind == 'small-start':
        return random.choice(['', "'", '“', '(', '_']) + f'{small} {left} {right}'
    if kind == 'small-end':
        return f'{left} {right} {small}' + random.choice(['', '.', '?', "'", '”', '?!'])
    if kind == 'subphrase':
        return f'{left}{random.choice(MARKS)} {small} {right}'
    if kind == 'names':
        return f'{random.choice(NAMES)} {left} {right}'
    if kind == 'mixed-case':
        return f'{left} {random.choice(["iPhone", "eBay", "OmniFocus", "AT&T", "Q&A", "éBay"])} {small} {right}'
    if kind == 'dotted':
        return f'{left} {random.choice(["example.com", "v1.2", "3.x", "in.a", "a.b", "http://localhost", "https://foo.com/a-b"])} {right}'
    if kind == 'initials':
        return f'{left} {random.choice(["A.B", "D.C.", "É.À", "A.B.C", "U.S.A.", "ABCD"])} {small} {right}'.upper()
    if kind == 'consonants':
        return f'{left} {random.choice(["cnn", "st", "nth", "rhythm", "tv", "fbi", "ſql", "KKK"])} {right}'
    if kind == 'slash':
        return f'{left} {small}/{right} {random.choice(["and/or", "tcp/ip", "/the", "the/", "x//y"])}'
    if kind == 'hyphen':
        return f'{left} {right}-{small}-{word()} {random.choice(["a-b", "the-the", "to-do", "end-to-end", "-the-"])}'
    if kind == 'leading-space':
        return random.choice(SPACES) + f'{small} {left} {right}'
    if kind == 'trailing-space':
        return f'{left} {right} {small}' + random.choice(SPACES)
    if kind == 'unicode-space':
        return random.choice(SPACES).join([small, left, random.choice(NAMES), right, random.choice(SMALL)])
    if kind == 'unicode-case':
        text = f'{random.choice(SPECIAL)} {left} {small} {random.choice(SPECIAL)} {right}'
        return text.upper() if random.random() < .5 else text
    if kind == 'combining':
        return f'{left} {random.choice(["o\u0027a\u0301", "a\u0301.b", "_a\u0301", "mc_foo", "\u200cword", "word\u0301"])} {right}'
    if kind == 'punctuation':
        return f'{random.choice(["«", "“", "’", "_", "[", "¿", "<"])}{left} {small} {right}{random.choice(["’", ")", "...", "?!", ":"])}'
    if kind == 'digit-prefix':
        return f'{random.randint(0, 999)}{left} {small} {right} {random.choice(["34th", "5TH", "2lmc", "1.2"])}'
    return f'{left} mc{small}-{right}/{word()} {random.choice(["x. v. a b", "vs. a b: vs. a", "mcmcthe", "mcfoo-bar"])}'


def write_set(prefix, records):
    data = ROOT / 'tests/data'
    inputs = ''.join(text + '\n' for text, _, _ in records).encode()
    answers = ''.join(answer + '\n' for _, answer, _ in records).encode()
    (data / f'{prefix}inputs.txt').write_bytes(inputs)
    (data / f'{prefix}expected.txt').write_bytes(answers)
    return {'count': len(records), 'categories': dict(sorted(Counter(kind for _, _, kind in records).items())), 'inputs_sha256': hashlib.sha256(inputs).hexdigest(), 'expected_sha256': hashlib.sha256(answers).hexdigest()}


def main():
    digest = hashlib.sha256(Path(titlecase.__file__).read_bytes()).hexdigest()
    if digest != 'a3d0b99857c7672b9a13ec9df54aa187082be7d39b202dc0511e67e6f7873ef0':
        raise RuntimeError('The reference source is not the pinned snapshot')
    if sys.version_info[:3] != (3, 12, 14) or regex.__version__ != '2026.11.9' or not titlecase.REGEX_AVAILABLE:
        raise RuntimeError('Use CPython 3.12.14 with regex==2026.11.9')
    random.seed(1)
    records, seen_inputs, seen_outputs = [], set(), set()
    counts = Counter()
    while len(records) < 4000:
        kind = TYPES[len(records) % len(TYPES)]
        text = make(kind)
        answer = titlecase.titlecase(text)
        if text in seen_inputs or answer in seen_outputs or '\r' in text or '\n' in text or '\r' in answer or '\n' in answer:
            continue
        records.append((text, answer, kind))
        seen_inputs.add(text)
        seen_outputs.add(answer)
        counts[kind] += 1
    random.shuffle(records)
    manifest = {'author': 'Kushal', 'seed': 1, 'reference_commit': '42f43e2de55bf003b286c6f8e8d8b2d26676a167', 'python': '3.12.14', 'regex': regex.__version__, 'reference_sha256': hashlib.sha256(Path(titlecase.__file__).read_bytes()).hexdigest(), 'visible': write_set('', records[:2000]), 'hidden': write_set('hidden_', records[2000:])}
    (ROOT / 'tests/data/manifest.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps(manifest, indent=2))


if __name__ == '__main__':
    main()

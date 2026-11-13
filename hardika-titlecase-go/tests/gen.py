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

NOUNS = 'atlas notebook horizon passage eclipse harbor chapter pebble autumn orbit trail cloud willow quartz letter reed song field vessel violet lantern summit ocean'.split()
SMALL = 'a an and as at but by en for if in of on or the to v v. via vs vs.'.split()
TOKENS = {
    'names': ["d'artagnan", "l'GranGe", "o‘neil", "o's'", "D'ANGELO", 'mcfoo-bar', 'mcthe', 'Mc_x', 'MCBY', 'mr', 'DR', 'Mss', 'macarthur'],
    'brands': ['iTunes', 'LaTeX', 'GitHub', 'AT&T', 'eBay', 'éBay', 'Σigma', 'ǅWord', 'PPPoE'],
    'domains': ['http://localhost', 'https://foo.com', 'example.org/a-b', 'a.b', '3.x', 'v1.2', 'in.a', 'A.BC.', 'É.À.'],
    'acronyms': ['bbc', 'npr', 'sql', 'st', 'tv', 'rhythm', 'y', 'ſql', 'KKK', 'NASA'],
    'unicode': ['ß', 'ΟΣ', 'ΑΣ', 'İ', 'ǰ', 'ﬁ', 'ﬃ', 'ᾇ', 'niño', '𐐨', '𞤢', 'ᏸ', 'a\u0301', 'o\u0027a\u0301', 'mc\u0301a', '\u2060word'],
}
JOINS = [' ', ' ', '\t', '  ', '\u00a0', '\u2007', '\u200a', '\u202f', '\u3000', '\x0c', '\u0085', '\u2029']
BREAKS = [': ', '. ', '; ', '? ', '! ', '- ', '– ', '‒ ', '— ', '― ']
FAMILIES = ['names', 'brands', 'domains', 'acronyms', 'unicode', 'compounds', 'subphrases', 'edges']


def phrase():
    return [random.choice(NOUNS), random.choice(SMALL), random.choice(NOUNS)]


def compose(family):
    pieces = phrase()
    if family in TOKENS:
        pieces.insert(random.randrange(len(pieces) + 1), random.choice(TOKENS[family]))
    elif family == 'compounds':
        middle = random.choice(SMALL)
        nested = random.choice([f'mc{middle}', random.choice(TOKENS['names']), random.choice(TOKENS['unicode'])])
        pieces[1] = random.choice([f'{nested}-{middle}/{pieces[2]}', f'{pieces[0]}/{middle}-{nested}', f'-{middle}-{nested}-', f'{nested}//{middle}'])
    elif family == 'subphrases':
        pieces[1] = random.choice([f'x. v. {random.choice(SMALL)}', 'vs. a b: vs. a', f'{random.choice(SMALL)}. {random.choice(SMALL)}'])
        pieces[0] += random.choice(BREAKS)
    else:
        pieces = [random.choice(SMALL), *pieces, random.choice(SMALL)]
    separator = random.choice(JOINS)
    text = separator.join(pieces)
    decoration = random.randrange(6)
    if decoration == 0:
        text = random.choice(["'", '“', '[', '_', '¿', '«', '’']) + text
    elif decoration == 1:
        text += random.choice(['?', '!', "'", '?!', '...', '”'])
    elif decoration == 2:
        text = random.choice(JOINS) + text
    elif decoration == 3:
        text += random.choice(JOINS)
    style = random.randrange(5)
    if style == 0:
        text = text.upper()
    elif style == 1:
        text = text.lower()
    elif style == 2:
        text = ''.join(char.upper() if random.random() < .2 else char for char in text)
    return text, f'{family}/{["upper", "lower", "mixed", "original", "original"][style]}'


def save(prefix, records):
    data = ROOT / 'tests/data'
    payloads = {'inputs': ''.join(record[0] + '\n' for record in records).encode(), 'expected': ''.join(record[1] + '\n' for record in records).encode()}
    report = {'count': len(records), 'categories': dict(sorted(Counter(record[2] for record in records).items()))}
    for name, payload in payloads.items():
        (data / f'{prefix}{name}.txt').write_bytes(payload)
        report[f'{name}_sha256'] = hashlib.sha256(payload).hexdigest()
    return report


def main():
    digest = hashlib.sha256(Path(titlecase.__file__).read_bytes()).hexdigest()
    if digest != 'a3d0b99857c7672b9a13ec9df54aa187082be7d39b202dc0511e67e6f7873ef0':
        raise RuntimeError('The reference source is not the pinned snapshot')
    if sys.version_info[:3] != (3, 12, 14) or regex.__version__ != '2026.11.9' or not titlecase.REGEX_AVAILABLE:
        raise RuntimeError('Use CPython 3.12.14 with regex==2026.11.9')
    random.seed(1)
    records, inputs, outputs = [], set(), set()
    while len(records) < 4000:
        family = FAMILIES[len(records) % len(FAMILIES)]
        text, label = compose(family)
        answer = titlecase.titlecase(text)
        if text in inputs or answer in outputs or '\r' in text or '\n' in text or '\r' in answer or '\n' in answer:
            continue
        inputs.add(text)
        outputs.add(answer)
        records.append((text, answer, label))
    random.shuffle(records)
    report = {'author': 'Hardika', 'seed': 1, 'reference_commit': '42f43e2de55bf003b286c6f8e8d8b2d26676a167', 'python': '3.12.14', 'regex': regex.__version__, 'reference_sha256': hashlib.sha256(Path(titlecase.__file__).read_bytes()).hexdigest(), 'visible': save('', records[:2000]), 'hidden': save('hidden_', records[2000:])}
    (ROOT / 'tests/data/manifest.json').write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()

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

LEXICON = 'tapestry observatory manuscript sonata pavilion sculpture itinerary fresco symposium mosaic curator estuary folklore chronicle promenade expedition conservatory prism concerto artisan'.split()
SMALL = 'a an and as at but by en for if in of on or the to v v. via vs vs.'.split()
FAMILIES = ['opening', 'closing', 'apostrophe', 'mc-chain', 'honorific', 'brand', 'dotted', 'initials', 'consonants', 'slash', 'hyphen', 'nested', 'subphrase', 'unicode', 'spacing', 'punctuation']
SPACES = [' ', '\t', '\u00a0', '\u2003', '\u2009', '\u202f', '\u3000', '\v', '\f', '\u0085', '\u2028', '\u2029']


def compose(family):
    left, right, extra = random.sample(LEXICON, 3)
    small = random.choice(SMALL)
    focus = {
        'opening': f'{small} {left}',
        'closing': f'{left} {small}',
        'apostrophe': random.choice(["d'este", "l‘auberge", "o'connor", "d'azur's", "o'a\u0301", "l'grange"]),
        'mc-chain': 'mc' * random.randint(1, 12) + random.choice(['the', 'and', 'ocean', 'ß', 'ſql', 'É.À']),
        'honorific': random.choice(['mr', 'Mrs', 'MSS', 'dR', 'ms']),
        'brand': random.choice(['OpenAI', 'iPad', 'YouTube', 'PowerPoint', 'ǅCase', 'éPrint']),
        'dotted': random.choice(['catalog.art', '2.x', 'a.b', 'edition.v2', 'a.ſ', 'in.a']),
        'initials': random.choice(['A.B.C.', 'É.À', 'A.BC.', 'Σ.Ω.', 'A.B.C']),
        'consonants': random.choice(['brr', 'psst', 'sql', 'rhythms', 'ſql', 'KKK', 'xyz']),
        'slash': f'{small}/{extra}',
        'hyphen': f'{extra}-{small}-{left}',
        'nested': f'mc{small}/{extra}-{small}/mc{right}',
        'subphrase': random.choice(['x. v. a', 'vs. a b: vs. a', f'{extra}: {small}', f'{extra}— {small}']),
        'unicode': random.choice(['ΣΟΣ', 'ΑΣ\u0301', 'İ', 'ß', 'ᾇ', 'ﬄ', 'ǰ', '𐐨', '𞤢', '\u0301a', 'mc\u0301a']),
        'spacing': random.choice(SPACES) + small + random.choice(SPACES),
        'punctuation': random.choice(['“', '[', "'", '_', '«', '¿']) + small + random.choice(['?!', "'", '”', '.', '!']),
    }[family]
    if family == 'opening':
        title = f'{focus} {right} {extra}'
    elif family == 'closing':
        title = f'{right} {extra} {focus}'
    else:
        title = f'{left} {focus} {small} {right} {extra}'
    if random.random() < .3:
        title = title.replace(' ', random.choice(SPACES))
    style = random.randrange(4)
    if style == 0:
        title = title.upper()
    elif style == 1:
        title = title.lower()
    if random.random() < .15:
        title = random.choice([' ', '\t', '\u2003']) + title
    if random.random() < .15:
        title += random.choice([' ', '\t', '\u2003'])
    return title


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
    visible, hidden, inputs, outputs = [], [], set(), set()
    for family in FAMILIES:
        records = []
        while len(records) < 250:
            text = compose(family)
            answer = titlecase.titlecase(text)
            if text in inputs or answer in outputs or '\r' in answer or '\n' in answer:
                continue
            inputs.add(text)
            outputs.add(answer)
            records.append((text, answer, family))
        random.shuffle(records)
        visible.extend(records[:125])
        hidden.extend(records[125:])
    random.shuffle(visible)
    random.shuffle(hidden)
    report = {'author': 'Komal', 'seed': 1, 'reference_commit': '42f43e2de55bf003b286c6f8e8d8b2d26676a167', 'python': '3.12.14', 'regex': regex.__version__, 'reference_sha256': hashlib.sha256(Path(titlecase.__file__).read_bytes()).hexdigest(), 'visible': save('', visible), 'hidden': save('hidden_', hidden)}
    (ROOT / 'tests/data/manifest.json').write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()

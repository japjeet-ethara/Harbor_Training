import argparse
import collections
import hashlib
import json
import random
import sys
from pathlib import Path


SEEDS = [
    ('public', 'the water desk welcomes {name} at {place}'),
    ('public', 'an access notice for {place}: {topic}'),
    ('public', 'bus diversions via {place} for {topic}'),
    ('public', 'library returns and {topic} with {name}'),
    ('public', 'a recycling briefing by {name} near {place}'),
    ('public', 'road repairs on the route to {place}: {topic}'),
    ('sports', '{name} hosts the {topic} fixture at {place}'),
    ('sports', 'the {place} cup: {topic} and the final'),
    ('sports', 'a warm-up for {topic} with {name}'),
    ('sports', '{topic} v. the {place} team with {name}'),
    ('sports', 'the {place} league vs. {topic} after the interval'),
    ('sports', 'a draw for {topic}; {name} announces the venue'),
    ('community', 'an open evening for {topic} at {place}'),
    ('community', '{name} introduces {topic} to the {place} choir'),
    ('community', 'the {place} garden club: {topic} for all'),
    ('community', 'a neighbourhood walk from {place} with {name}'),
    ('community', 'the craft exchange by {name}: {topic}'),
    ('community', '{topic} in the {place} hall with {name}'),
    ('everyday', 'a parcel for {name} at {place}: {topic}'),
    ('everyday', '{name} shares the {topic} timetable for {place}'),
    ('everyday', 'the lost property desk at {place} needs {topic}'),
    ('everyday', 'an invitation from {name} for {topic}'),
    ('everyday', 'the {place} kitchen welcomes {topic} after lunch'),
    ('everyday', '{topic} and the morning briefing by {name}'),
]
NAMES = ["d'arcy", "o'neill", 'l‘ouverture', "o'brien's", 'mcdonald', 'Mcintyre', 'MCLEOD',
         'mcgregor', 'mr', 'mRs', 'MS', 'dr', 'J.R.R.', 'A.B', 'iPhone', 'eBay', 'BBC', 'rhythm',
         'st', 'ſmith', 'İpek', 'ırem', 'ßara', 'ﬃona', 'ǰana', 'ΣΟΣ', 'AΣ', 'e\u0301va', 'ŉandi']
PLACES = ['riverside', 'meadow park', 'oak library', 'the old station', 'north harbour',
          'east community hall', 'maple school', 'cedar ground', 'canal bridge', 'elm square',
          'south clinic', 'hill pavilion', 'union gardens', 'willow market', 'west arena', 'stone quay']
TOPICS = [('small', 'the art of the walk'), ('small', 'an evening in the garden'),
          ('slash', 'arts/crafts'), ('slash', 'in/out-of-service'), ('hyphen', 'mother-in-law'),
          ('nested', 'north/south-east/west'), ('nested', 'by-the-sea/and-the-hill'),
          ('url', 'https://civic.example/help-desk'), ('inline', 'a.b timetable'),
          ('internal', 'eHealth updates'), ('consonants', 'RSPB talks'), ('consonants', 'bcd fixtures'),
          ('unicode', 'ßeta and ﬃlm'), ('context', 'ΟΣ and AΣ\u0301'),
          ('combining', '\u0301elm and e\u0301arth'), ('initials', 'J.P. and A.B.C'),
          ('boundary', 'the_guide and an\u0345nex'), ('prefix', 'andante via viaduct'),
          ('punctuation', '“the return”'), ('honorific', 'Dr and mRS'),
          ('apostrophe', "d'angelo and o‘reilly"), ('mc', 'Mcadams and mccall'),
          ('prefix', 'vs. versus v. visitor'), ('nested', 'a/b-c/d-e'),
          ('boundary', 'and\u200c or\u203f the\u2160'), ('unicode', 'İSTANBUL and ǳUNGLE')]
SPACES = [' ', '\t', '\v', '\f', '\u00a0', '\u1680', '\u2003', '\u2028', '\u2029', '\u202f', '\u205f', '\u3000', '\x1c', '\x85']
DIRECTED = ['', ' ', '\t', 'the', 'andante', ': andante', ': via', ': vs. the return', 'THE',
            "d'arcy", "l'art's", "o'brien", 'Mcadams', 'MCLEOD', 'McA', 'Dr', 'mRs', 'A.B.C',
            'iPhone', 'RSPB', 'rhythm', 'a/b-c/d', 'http://civic.example/a-b', 'ßeta', 'ﬃlm',
            'ǳUNGLE', 'ΟΣ', 'AΣ\u0301', '\u0345Σ', '\u0301elm', 'e\u0301va', 'Ⅰ.test', 'ſſſ',
            'the\u0345', '(the)', 'the!!', '“an”', '\\the', ']the', 'bcd', 'İSTANBUL', 'ŉandi']


def build():
    root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(root / 'tools'))
    from reference import load

    random.seed(1)
    ref = load()
    records, inputs, outputs = [], set(), set()
    rejected = collections.Counter()

    def add(text, tags):
        assert '\n' not in text and '\r' not in text
        if text in inputs:
            rejected['duplicate_input'] += 1
            return
        answer = ref.titlecase(text)
        if answer in outputs:
            rejected['duplicate_output'] += 1
            return
        inputs.add(text)
        outputs.add(answer)
        records.append(dict(input=text, expected=answer, tags=sorted(set(tags))))

    for text in DIRECTED:
        add(text, ['directed'])
    while len(records) < 4000:
        domain, template = random.choice(SEEDS)
        tag, topic = random.choice(TOPICS)
        other_tag, other = random.choice(TOPICS)
        name, place = random.choice(NAMES), random.choice(PLACES)
        text = template.format(name=name, place=place, topic=topic)
        tags = [domain, tag, 'name']
        if random.random() < .42:
            text += random.choice(['; ', ': ', ' - ', '? ', '! ', '. ']) + other
            tags += [other_tag, 'subphrase', 'interaction']
        mode = random.randrange(6)
        if mode == 0:
            text = text.upper()
            tags.append('allcaps')
        elif mode == 1:
            text = text.lower()
            tags.append('lower')
        elif mode == 2:
            text = text.swapcase()
            tags.append('mixed')
        if random.random() < .45:
            text = random.choice(['(', '[', '“', '!', "'"]) + text + random.choice([')', ']', '”', '!', '!!', '?'])
            tags.append('punctuation')
        if random.random() < .45:
            text = text.replace(' ', random.choice(SPACES))
            tags.append('whitespace')
        if random.random() < .12:
            text = random.choice([' ', '\t', '\u00a0']) + text + random.choice([' ', '\t', '\u2003'])
            tags.append('edge-space')
        add(text, tags)
    random.shuffle(records)
    return records, rejected


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, default=Path(__file__).parent / 'data')
    args = parser.parse_args()
    records, rejected = build()
    args.out.mkdir(parents=True, exist_ok=True)
    for prefix, rows in [('', records[:2000]), ('hidden_', records[2000:])]:
        for field, suffix in [('input', 'inputs.txt'), ('expected', 'expected.txt')]:
            path = args.out / (prefix + suffix)
            path.write_bytes(('\n'.join(r[field] for r in rows) + '\n').encode('utf-8'))
    visible, hidden = records[:2000], records[2000:]
    report = dict(seed=1, records=4000, visible=2000, hidden=2000,
                  input_overlap=len({r['input'] for r in visible} & {r['input'] for r in hidden}),
                  output_overlap=len({r['expected'] for r in visible} & {r['expected'] for r in hidden}),
                  rejected=dict(rejected),
                  counts={label:dict(collections.Counter(t for r in rows for t in r['tags'])) for label,rows in [('visible',visible),('hidden',hidden)]},
                  sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(args.out.glob('*.txt'))})
    (args.out / 'coverage.json').write_text(json.dumps(report, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    (args.out / 'records.json').write_text(json.dumps([dict(input=r['input'], tags=r['tags']) for r in records], ensure_ascii=True, separators=(',', ':'))+'\n', encoding='utf-8')
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()

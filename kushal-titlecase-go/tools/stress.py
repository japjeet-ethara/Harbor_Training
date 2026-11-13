import argparse
import hashlib
import json
import random
import subprocess
import sys
from pathlib import Path


def generate(reference, count):
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(reference))
    import titlecase
    if not titlecase.REGEX_AVAILABLE:
        raise RuntimeError('Install the pinned regex dependency')
    rng = random.Random(841763)
    normal = 'river story window lantern quiet harbor mountain signal note return garden'.split()
    small = 'a an and as at but by en for if in of on or the to v v. via vs vs.'.split()
    tricky = ["d'angelo", "l'grange", "o'grange's", "o's'", 'mcthe', 'mcby', 'MCFOO-BAR', 'mr', 'MRS', 'mss', 'iTunes', 'AT&T', 'in.a', 'v1.2', '3.x', 'a.b', 'A.BC.', 'http://localhost', 'http://foo.com', 'a-b', 'the-the', 'and/or', 'tcp/ip', 'x//y', '_the', '34th', 'ſql', 'KKK', 'ß', 'İ', 'ΟΣ', 'ΑΣ', 'ǅ', 'ᾀ', 'ﬁ', 'éBay', '\u0301a', 'a\u0301', '𐐨', '𞤢']
    separators = [' ', ' ', '\t', '  ', '\u00a0', '\u2003', '\u202f', '\u3000', '\x0b', '\x0c', '\x1c', '\u0085', '\u2028', '\u2029', ': ', '. ', '; ', '! ', '? ', '- ', '— ', '‒ ']
    lines, seen = [], set()
    def add(text):
        if text not in seen and '\n' not in text and '\r' not in text:
            seen.add(text)
            lines.append(text)
    for text in ['', ' ', '\t', ' the cat', 'the cat of ', 'x. v. a b', 'vs. a b: vs. a', 'mcthe', 'mcby', "o's'", 'a-b the-the']:
        add(text)
    for code in range(0x110000):
        if 0xD800 <= code <= 0xDFFF:
            continue
        char = chr(code)
        if char.upper() != char or char.lower() != char:
            for text in [char, f'{char}Σ', f'a{char}.b', f"o'{char}", f'word: {char} the', f'mc{char}a']:
                add(text)
    while len(lines) < count:
        tokens = []
        for _ in range(rng.randint(1, 8)):
            pool = rng.random()
            if pool < .3:
                token = rng.choice(small)
            elif pool < .6:
                token = rng.choice(tricky)
            elif pool < .9:
                token = rng.choice(normal)
            else:
                code = rng.randrange(0x110000)
                if 0xD800 <= code <= 0xDFFF:
                    code = 0x41
                token = chr(code) + rng.choice(normal)
            style = rng.randrange(7)
            if style == 0:
                token = token.upper()
            elif style == 1:
                token = token.lower()
            if rng.random() < .1:
                token = rng.choice(['“', '’', '«', '[', '_', '<', '¿']) + token
            tokens.append(token)
        text = rng.choice(separators).join(tokens)
        if rng.random() < .08:
            text = rng.choice(separators) + text
        if rng.random() < .08:
            text += rng.choice(separators)
        if rng.random() < .15:
            text = text.upper()
        add(text)
    lines = lines[:count]
    expected = [titlecase.titlecase(text) for text in lines]
    return lines, expected


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--reference', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--count', type=int, default=100000)
    parser.add_argument('binaries', nargs='*', type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    lines, expected = generate(args.reference, args.count)
    payload = ''.join(line + '\n' for line in lines).encode()
    answer_bytes = ''.join(line + '\n' for line in expected).encode()
    (args.output / 'inputs.txt').write_bytes(payload)
    (args.output / 'expected.txt').write_bytes(answer_bytes)
    report = {'seed': 841763, 'count': len(lines), 'inputs_sha256': hashlib.sha256(payload).hexdigest(), 'expected_sha256': hashlib.sha256(answer_bytes).hexdigest(), 'results': {}}
    for binary in args.binaries:
        result = subprocess.run([str(binary)], input=payload, capture_output=True, timeout=120)
        actual = result.stdout.split(b'\n')
        if actual and actual[-1] == b'':
            actual.pop()
        bad = [i for i, answer in enumerate(expected) if i >= len(actual) or actual[i] != answer.encode()]
        details = {'exit_code': result.returncode, 'output_lines': len(actual), 'mismatches': len(bad), 'score': (len(expected) - len(bad)) / max(len(expected), len(actual)), 'examples': [{'input': lines[i], 'expected': expected[i], 'actual': actual[i].decode(errors='replace') if i < len(actual) else None} for i in bad[:10]]}
        report['results'][binary.name] = details
    (args.output / 'report.json').write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps(report, indent=2, ensure_ascii=False))
    if any(result['mismatches'] or result['exit_code'] for result in report['results'].values()):
        raise SystemExit(1)


if __name__ == '__main__':
    main()

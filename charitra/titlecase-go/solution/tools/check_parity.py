#!/usr/bin/env python3
"""Differential checks against the pinned original; never hand-author answers.

Example:
  python3 -S solution/tools/check_parity.py \
    --source environment/repo --binary /tmp/titlecase-candidate --full-unicode

This is an authoring check, not the hidden grader. Run with Python 3.12 and -S
so an ambient third-party regex package cannot change the reference backend.
"""
import argparse
import importlib
from pathlib import Path
import random
import string
import subprocess
import sys
import unicodedata

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--source', required=True, type=Path)
parser.add_argument('--binary', required=True, type=Path)
parser.add_argument('--random-count', type=int, default=20000)
parser.add_argument('--full-unicode', action='store_true')
args = parser.parse_args()
if sys.version_info[:2] != (3, 12):
    raise SystemExit('Use Python 3.12 for the pinned reference semantics.')
sys.path.insert(0, str(args.source.resolve()))
original = importlib.import_module('titlecase')
if original.REGEX_AVAILABLE:
    raise SystemExit('Reference selected optional regex; run python3 -S instead.')
original_tests = importlib.import_module('titlecase.tests')
reference = original.titlecase
binary = str(args.binary.resolve())


def check_batch(name, samples, final_newline=True):
    samples = list(samples)
    assert all('\r' not in line and '\n' not in line for line in samples)
    raw = '\n'.join(samples)
    if samples and final_newline:
        raw += '\n'
    result = subprocess.run([binary], input=raw.encode('utf-8'), capture_output=True,
                            check=True, timeout=180)
    expected = ''.join(reference(line) + '\n' for line in samples).encode('utf-8')
    if result.stdout != expected:
        actual = result.stdout.split(b'\n')
        answers = expected.split(b'\n')
        failures = []
        for index in range(max(len(actual), len(answers))):
            got = actual[index] if index < len(actual) else None
            want = answers[index] if index < len(answers) else None
            if got != want:
                failures.append((index, samples[index] if index < len(samples) else None,
                                 want, got))
                if len(failures) == 10:
                    break
        for index, source, want, got in failures:
            print(f'line={index + 1} input={source!r} expected={want!r} actual={got!r}')
        raise SystemExit(f'{name}: mismatch')
    print(f'{name}: {len(samples)} inputs, exact bytes match')
    return len(samples)


count = check_batch('upstream default-function cases',
                    (case[0] for case in original_tests.TEST_DATA
                     if '\n' not in case[0] and '\r' not in case[0]))
count += check_batch('line framing, spacing and Unicode regressions', [
    '', ' ', '\t', '  the world  ', 'hello  and\tworld', 'the ﬃnal thing',
    'Mcßxyz', 'ΣΟΣ', 'ΟΣ', 'ΟΣ\u0345', 'İF ÎN of ıF', 'mſ', '_hello',
    "D'ARTAGNAN", 'https://localhost/foo', 'foo!  an ending', 'foo!\tan ending',
    'foo\u2028bar', 'foo\x1cbar', 'word' * 20000,
])
count += check_batch('final record without LF', ['the lord of the rings', 'a final title'], False)
check_batch('empty input stream', [])
rng = random.Random(20261106)
tokens = ['a', 'an', 'and', 'as', 'at', 'but', 'by', 'en', 'for', 'if', 'in', 'of',
          'on', 'or', 'the', 'to', 'v', 'v.', 'via', 'vs', 'vs.', 'word', 'foo',
          'bar', 'NASA', 'iPhone', 'McDonald', 'mcfoo', 'mCfoo', 'MCFOO',
          "d'artagnan", "D'ARTAGNAN", "o'malley", "l'amour", 'foo.com', '1.2',
          '1A', 'ß', 'ﬃ', 'ΟΣ', 'ΑΣΑ', 'İF', 'ıf', 'ſsh', 'KGB', '\u0345',
          'Ånd', 'école', 'ÜBER']
separators = [' ', '  ', '\t', '\xa0', '-', '/', '//', ': ', '! ', '?  ', ';\t', '— ']
samples = []
for _ in range(args.random_count):
    line = rng.choice(tokens)
    for __ in range(rng.randrange(1, 8)):
        line += rng.choice(separators) + rng.choice(tokens)
    if rng.random() < 0.2:
        line = line.upper()
    if rng.random() < 0.2:
        line = rng.choice([' ', "'", '“', '(', '_', '[']) + line + rng.choice([' ', ')', "'", ']'])
    samples.append(line)
count += check_batch('seeded combinations of rule interactions', samples)
rng = random.Random(914)
alphabet = list(string.ascii_letters + string.digits + string.punctuation + '\t ')
alphabet += list('éÉáÁñÑöÖßİıſKΣσς\u0345\u0301ﬃﬄ\u02b0‘’“”–—‒―\u00a0\u1680\u2000\u200d\u2028\u2029\u3000\x1c\x1d\x1e\x1f\x85')
count += check_batch('seeded character fuzz',
                     (''.join(rng.choice(alphabet) for __ in range(rng.randrange(50)))
                      for _ in range(args.random_count * 5)))
samples = []
for n in range(0x110000):
    if 0xD800 <= n <= 0xDFFF or n in (10, 13):
        continue
    ch = chr(n)
    if ch.upper() != ch or ch.lower() != ch or ch.title() != ch or ch.isalnum() and not ch.isalpha():
        samples.extend([ch, 'the ' + ch + ' and', 'AΣ' + ch + 'A', 'AΣ' + ch + ' ',
                        ' ' + ch + 'Σ', 'mc' + ch + 'test', "d'" + ch + 'word'])
count += check_batch('case-changing and numeric Unicode interactions', samples)
if args.full_unicode:
    count += check_batch('every single valid Unicode scalar except CR/LF',
                         (chr(n) for n in range(0x110000)
                          if not 0xD800 <= n <= 0xDFFF and n not in (10, 13)))
print(f'PASS: {count} differential records; Python {sys.version.split()[0]}, '
      f'Unicode {unicodedata.unidata_version}, re backend')
print('These finite checks provide evidence of parity, not a proof for every string.')

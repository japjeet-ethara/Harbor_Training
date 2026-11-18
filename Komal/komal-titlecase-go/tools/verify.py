import hashlib
import json
import os
import platform
import random
import subprocess
import tempfile
import time
from pathlib import Path
from reference import ROOT, digest, load


def command(args, **kwargs):
    print('$ ' + ' '.join(map(str, args)), flush=True)
    return subprocess.run(args, check=True, timeout=600, **kwargs)


def records(path):
    data = path.read_bytes()
    assert data.endswith(b'\n')
    return data[:-1].split(b'\n')


def main():
    started = time.monotonic()
    ref = load()
    print(f'CPython {platform.python_version()}; Unicode 15.0.0; regex installed: {ref.REGEX_AVAILABLE}', flush=True)
    command(['go', 'version'])
    data = ROOT / 'titlecase-go/tests/data'
    with tempfile.TemporaryDirectory() as temp:
        temp = Path(temp)
        runs = []
        for label in ['regen-a', 'regen-b']:
            output = temp / label
            command(['python', str(ROOT / 'titlecase-go/tests/gen.py'), '--out', str(output)], stdout=subprocess.DEVNULL)
            runs.append({p.name: digest(p) for p in sorted(output.iterdir())})
        assert runs[0] == runs[1]
        assert runs[0] == {p.name: digest(p) for p in sorted(data.iterdir())}
        print('Dataset regeneration twice: all six files byte identical to frozen files', flush=True)
        for prefix in ['', 'hidden_']:
            inputs = records(data / (prefix + 'inputs.txt'))
            expected = records(data / (prefix + 'expected.txt'))
            assert len(inputs) == len(expected) == 2000
            actual = [ref.titlecase(s.decode('utf-8')).encode('utf-8') for s in inputs]
            assert actual == expected
            print(f'{prefix or "visible_"}all 2000 frozen answers re-executed against original: exact', flush=True)
        tables = temp / 'tables.json'
        command(['python', str(ROOT / 'tools/gen_unicode.py'), str(tables)])
        assert tables.read_bytes() == (ROOT / 'titlecase-go/solution/internal/pyunicode/tables.json').read_bytes()
        print('Fresh Unicode regeneration: byte identical', flush=True)
        solution = ROOT / 'titlecase-go/solution'
        command(['go', 'test', './...', '-v'], cwd=solution)
        command(['go', 'vet', './...'], cwd=solution)
        command(['go', 'build', './...'], cwd=solution)
        executable = temp / 'titlecase'
        command(['go', 'build', '-o', str(executable), '.'], cwd=solution)
        for prefix in ['', 'hidden_']:
            payload = (data / (prefix + 'inputs.txt')).read_bytes()
            result = command([str(executable)], input=payload, capture_output=True)
            assert result.stdout == (data / (prefix + 'expected.txt')).read_bytes()
            assert result.stderr == b''
            print(f'{prefix or "visible_"}2000/2000 Go records: exact bytes and LF framing', flush=True)
        rng = random.Random(871231)
        alphabet = list("abceinorstuvxyzABCDIMNRSTV./-:'‘“”!_\\[]()123") + list('éßﬃǳǰİıſKΣΟΣ\u0301\u0345\u200c\u2160\U00010428\U0001f680')
        words = ['the', 'and', 'via', 'vs.', 'v.', 'an', 'andante', 'mcdonald', 'McA', 'MCAB', "d'arcy", "o'neill's", 'BBC', 'bcd', 'iPhone', 'a.b', 'A.B.C', 'mRS', 'Dr', 'the!!', 'a/b-c/d', 'AΣ\u0345', 'ΟΣ', 'ßeta']
        separators = [' ', '\t', '\v', '\x1c', '\x85', '\u00a0', '\u2028', '\u202f']
        cases, seen = [], set()
        while len(cases) < 110000:
            mode = rng.randrange(4)
            if mode == 0:
                s = ''.join(rng.choices(alphabet, k=rng.randrange(1, 65)))
            elif mode == 1:
                terms = rng.choices(words, k=rng.randrange(1, 9))
                s = rng.choice(separators).join(terms)
            elif mode == 2:
                scalar = rng.randrange(0x110000)
                if scalar in (10, 13) or 0xD800 <= scalar <= 0xDFFF:
                    continue
                c = chr(scalar)
                s = rng.choice(['AΣ', 'Mc', "o'", ': an', 'the ', '', 'ß']) + c + rng.choice(['Σ', ' and the', '/in-law', '.a', '', 'A'])
            else:
                s = ''.join(rng.choices(alphabet, k=rng.randrange(1, 12))) + rng.choice(['/', '-', '/a-', '-Mc', '//']) + rng.choice(words)
            if rng.randrange(5) == 0:
                s = s.upper()
            if s not in seen:
                seen.add(s)
                cases.append(s)
        payload = ('\n'.join(cases) + '\n').encode('utf-8')
        expected = ('\n'.join(ref.titlecase(s) for s in cases) + '\n').encode('utf-8')
        result = command([str(executable)], input=payload, capture_output=True)
        if result.stdout != expected:
            actual = result.stdout.split(b'\n')
            answers = expected.split(b'\n')
            failures = []
            for i, s in enumerate(cases):
                got = actual[i] if i < len(actual) else b'<missing>'
                if got != answers[i]:
                    failures.append(dict(index=i, input=s, expected=answers[i].decode('utf-8'), actual=got.decode('utf-8', errors='replace')))
                    if len(failures) == 20:
                        break
            print(json.dumps(failures, ensure_ascii=True, indent=2))
            raise AssertionError('differential stress mismatch')
        assert result.stderr == b''
        print(json.dumps(dict(stress_cases=len(cases), unique=len(seen), mismatches=0,
                              seed=871231, input_sha256=hashlib.sha256(payload).hexdigest(),
                              expected_sha256=hashlib.sha256(expected).hexdigest(),
                              elapsed_seconds=time.monotonic()-started), indent=2), flush=True)


if __name__ == '__main__':
    main()

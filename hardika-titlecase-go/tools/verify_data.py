import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / 'environment/reference'))
import regex
import titlecase


def hashes():
    return {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted((ROOT / 'tests/data').glob('*')) if path.is_file()}


def main():
    original = hashes()
    for _ in range(2):
        subprocess.run([sys.executable, str(ROOT / 'tests/gen.py')], check=True, stdout=subprocess.DEVNULL)
        if hashes() != original:
            raise RuntimeError('Dataset generation changed a frozen file')
    report = {'deterministic_runs': 2, 'splits': {}, 'input_overlap': None, 'output_overlap': None}
    sets = {}
    for prefix in ['', 'hidden_']:
        inputs = (ROOT / f'tests/data/{prefix}inputs.txt').read_bytes().split(b'\n')[:-1]
        expected = (ROOT / f'tests/data/{prefix}expected.txt').read_bytes().split(b'\n')[:-1]
        if len(inputs) != 2000 or len(expected) != 2000:
            raise RuntimeError('Expected 2000 input and output records')
        if any(titlecase.titlecase(value.decode()).encode() != answer for value, answer in zip(inputs, expected)):
            raise RuntimeError('A frozen answer differs from the reference')
        sets[prefix] = set(inputs), set(expected)
        report['splits'][prefix or 'visible'] = {'records': len(inputs), 'reference_agreement': len(expected), 'unique_inputs': len(set(inputs)), 'unique_outputs': len(set(expected))}
    report['input_overlap'] = len(sets[''][0] & sets['hidden_'][0])
    report['output_overlap'] = len(sets[''][1] & sets['hidden_'][1])
    if report['input_overlap'] or report['output_overlap']:
        raise RuntimeError('Visible and hidden sets overlap')
    (ROOT / 'evidence/dataset-verification.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()

import sys
from pathlib import Path
from rewardkit import criterion
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _shared import DATA, command, fraction, isolated, prepare

@criterion
def behaviour(workspace: Path) -> dict:
    if not prepare(workspace):
        return {'score': 0.0, 'reasoning': 'Go build did not pass'}
    binary = Path('/tmp/candidate-filter')
    try:
        binary.unlink(missing_ok=True)
        code, _, _ = command(['go', 'build', '-o', str(binary), '.'], workspace)
        if code or not binary.is_file():
            return {'score': 0.0, 'reasoning': 'Root package did not produce a program'}
        payload = (DATA / 'hidden_inputs.txt').read_bytes()
        expected = (DATA / 'hidden_expected.txt').read_bytes()
        actual = isolated(binary, payload)
        if actual is None:
            return {'score': 0.0, 'reasoning': 'Program failed or exceeded execution limits'}
        score = fraction(actual, expected)
        return {'score': score, 'reasoning': f'{score:.6f} exact line agreement'}
    except (OSError, ValueError):
        return {'score': 0.0, 'reasoning': 'Could not build or execute the submission'}

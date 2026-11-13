import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / 'environment/reference'))
from titlecase import titlecase

CASES = [b'', b'\n', b'\n\n', b'a thing', b'a thing\n', b'a\r\nb\r\n', b'a\n\nb\n', b'  a thing  \n', b'a\tb\n', 'ΟΣ ß İ ﬁ\n'.encode(), 'a\u2028b\n'.encode(), "l'grange\nmcby\n".encode(), b'word: THE title\n', b'word\x00text\n']


@pytest.mark.parametrize('payload', CASES)
def test_line_contract(payload):
    binary = os.getenv('TITLECASE_BINARY')
    if not binary:
        pytest.skip('Set TITLECASE_BINARY to a built program')
    records = payload.split(b'\n')
    if records[-1] == b'':
        records.pop()
    expected = b''.join((titlecase(record.removesuffix(b'\r').decode()) + '\n').encode() for record in records)
    result = subprocess.run([binary], input=payload, capture_output=True, timeout=10)
    assert result.returncode == 0
    assert result.stdout == expected

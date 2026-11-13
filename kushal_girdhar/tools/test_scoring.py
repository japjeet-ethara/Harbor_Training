import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('scoring', ROOT / 'tests/checks/_shared.py')
SCORING = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SCORING)


def test_exact_stream():
    assert SCORING.fraction(b'One\nTwo\n', b'One\nTwo\n') == 1


def test_extra_lines_reduce_credit():
    assert SCORING.fraction(b'One\nExtra\n', b'One\n') == .5


def test_missing_final_newline_is_a_mismatch():
    assert SCORING.fraction(b'One\nTwo', b'One\nTwo\n') == .5


def test_blank_line_is_not_empty_input():
    assert SCORING.fraction(b'', b'\n') == 0


def test_empty_streams_agree():
    assert SCORING.fraction(b'', b'') == 1


def test_unicode_separators_stay_in_the_record():
    text = 'A\u2028B\n'.encode()
    assert len(SCORING.byte_lines(text)) == 1
    assert SCORING.fraction(text, b'A\nB\n') == 0


def test_whitespace_is_compared_as_bytes():
    assert SCORING.fraction('A\u00a0B\n'.encode(), b'A B\n') == 0


def test_shifted_output_does_not_get_unordered_credit():
    assert SCORING.fraction(b'Two\nOne\n', b'One\nTwo\n') == 0

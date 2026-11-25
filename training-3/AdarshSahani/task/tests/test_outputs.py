"""Unit tests for verifier record parsing and scoring."""

import sys
import types
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "checks" / "behaviour"))

# The verifier installs Reward Kit as an isolated uv tool. These unit tests need
# only the criterion decorator, so provide a no-op stub in this process.
if "rewardkit.session" not in sys.modules:
    rewardkit = types.ModuleType("rewardkit")
    rewardkit.__path__ = []
    session = types.ModuleType("rewardkit.session")
    session.criterion = lambda **kwargs: (lambda fn: fn)
    rewardkit.session = session
    sys.modules["rewardkit"] = rewardkit
    sys.modules["rewardkit.session"] = session

from behaviour import _records, _score


class RecordProtocolTests(unittest.TestCase):
    def test_empty_input_has_zero_records(self):
        self.assertEqual(_records(b""), [])

    def test_blank_record_is_not_empty_input(self):
        self.assertEqual(_records(b"\n"), [b""])

    def test_lf_and_crlf_input_records(self):
        self.assertEqual(_records(b"one\ntwo\n", allow_crlf=True), [b"one", b"two"])
        self.assertEqual(_records(b"one\r\ntwo\r\n", allow_crlf=True), [b"one", b"two"])

    def test_missing_final_lf_is_malformed(self):
        with self.assertRaises(ValueError):
            _records(b"one")

    def test_bare_cr_is_malformed(self):
        with self.assertRaises(ValueError):
            _records(b"one\rtwo\n")

    def test_echo_scores_zero(self):
        self.assertEqual(_score(b"Known\nlower\n", b"Known\nLower\n", b"Known\nlower\n"), 0.0)

    def test_undiscriminating_nonempty_suite_scores_zero(self):
        self.assertEqual(_score(b"Same\n", b"Same\n", b"Same\n"), 0.0)

    def test_correct_output_scores_one(self):
        self.assertEqual(_score(b"Known\nlower\n", b"Known\nLower\n", b"Known\nLower\n"), 1.0)

    def test_missing_and_extra_records_are_rejected(self):
        self.assertEqual(_score(b"a\nb\n", b"A\nB\n", b"A\n"), 0.0)
        self.assertEqual(_score(b"a\n", b"A\n", b"A\nextra\n"), 0.0)

    def test_malformed_outputs_are_rejected(self):
        self.assertEqual(_score(b"a\n", b"A\n", b"\xff\n"), 0.0)
        self.assertEqual(_score(b"a\n", b"A\n", b"A\r\n"), 0.0)
        self.assertEqual(_score(b"a\n", b"A\n", b"A"), 0.0)

    def test_empty_stream_and_blank_record(self):
        self.assertEqual(_score(b"", b"", b""), 1.0)
        self.assertEqual(_score(b"\n", b"\n", b"\n"), 0.0)


if __name__ == "__main__":
    unittest.main()

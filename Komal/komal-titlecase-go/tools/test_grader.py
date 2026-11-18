import importlib.util
import unittest
from pathlib import Path

path = Path(__file__).resolve().parents[1] / 'titlecase-go/tests/_grader.py'
spec = importlib.util.spec_from_file_location('grader', path)
grader = importlib.util.module_from_spec(spec)
spec.loader.exec_module(grader)


class ScoringTests(unittest.TestCase):
    def test_exact_bytes(self):
        self.assertEqual(grader.compare_output(b'a\nb \n', b'a\nb \n', True)[0], 1)
        self.assertEqual(grader.compare_output(b'a\nb\n', b'a\nb \n', True)[0], .5)
        self.assertEqual(grader.compare_output('é\n'.encode(), 'e\u0301\n'.encode(), True)[0], 0)
        self.assertEqual(grader.compare_output(b'a\r\n', b'a\n', True)[0], 0)

    def test_framing(self):
        self.assertEqual(grader.compare_output(b'a\n', b'a\nb\n', True)[0], .5)
        self.assertAlmostEqual(grader.compare_output(b'a\nb\nx\n', b'a\nb\n', True)[0], 2/3)
        self.assertEqual(grader.compare_output(b'a\nb', b'a\nb\n', True)[0], 0)
        self.assertEqual(grader.compare_output(b'', b'a\nb\n', True)[0], 0)
        self.assertEqual(grader.compare_output(b'\n', b'\n', True)[0], 1)

    def test_failure_and_baseline_math(self):
        self.assertEqual(grader.compare_output(b'a\n', b'a\n', False)[0], 0)
        self.assertEqual((0+0+4*0)/6, 0)
        self.assertAlmostEqual((1+0+4*0)/6, 1/6)
        self.assertEqual((1+1+4*1)/6, 1)
        self.assertGreater((1+0+4*.5)/6, 1/6)


if __name__ == '__main__':
    unittest.main(verbosity=2)

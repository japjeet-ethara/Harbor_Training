#!/usr/bin/env python3
"""Host-safe tests for grader logic; every Worker.run is mocked.

These are local logic checks, not Harbor/Docker or privilege-boundary evidence.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

os.environ["LITELLM_LOCAL_MODEL_COST_MAP"] = "True"
TASK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TASK / "tests"))
import grader
from rewardkit import WorkerError, WorkerResult, WorkerSetupError


def go_metadata(*, main: bool = True, external: bool = False, require: bool = False):
    root = {"Name": "main" if main else "library", "Module": {"Main": True}}
    deps = [{"ImportPath": "fmt", "Standard": True}, root]
    if external:
        deps.append({"ImportPath": "example.net/external", "Module": {"Main": False}})
    return {
        "root.json": json.dumps(root).encode(),
        "deps.json": b"\n".join(json.dumps(item).encode() for item in deps),
        "module.json": json.dumps({"Require": [{"Path": "example.net/external"}] if require else []}).encode(),
        "candidate": b"fake binary; intentionally never executed by local tests",
    }


class RecordTests(unittest.TestCase):
    def test_empty_records_and_whitespace_are_preserved(self):
        self.assertEqual(grader.lf_records(b"\n a \n\t\n"), [b"", b" a ", b"\t"])
        self.assertEqual(grader.score_records(b"a \n", [b"a"])[0], 0)
        self.assertEqual(grader.score_records(b"a\r\n", [b"a"])[0], 0)

    def test_unicode_line_separator_is_not_an_lf(self):
        record = "a\u2028b\u0085c".encode()
        self.assertEqual(grader.lf_records(record + b"\n"), [record])

    def test_missing_and_extra_records_receive_zero(self):
        expected = [b"a", b"b"]
        self.assertEqual(grader.score_records(b"a\n", expected)[0], 0)
        self.assertEqual(grader.score_records(b"a\nb\nextra\n", expected)[0], 0)
        self.assertEqual(grader.score_records(b"a\nb", expected)[0], 0)
        self.assertEqual(grader.score_records(b"", expected)[0], 0)

    def test_fraction_is_byte_exact(self):
        self.assertEqual(grader.score_records(b"a\nb \n", [b"a", b"b"])[:3], (0.5, 1, 2))

    def test_utf8_equivalence_is_not_normalized(self):
        self.assertEqual(grader.score_records("é\n".encode(), ["e\u0301".encode()])[0], 0)


class AuditTests(unittest.TestCase):
    def test_root_main_with_stdlib_and_own_module_passes(self):
        self.assertTrue(grader.audit_go_metadata(go_metadata())[0])

    def test_external_dependency_even_if_vendored_fails(self):
        self.assertFalse(grader.audit_go_metadata(go_metadata(external=True))[0])

    def test_unused_external_require_also_fails(self):
        self.assertFalse(grader.audit_go_metadata(go_metadata(require=True))[0])

    def test_root_library_fails(self):
        self.assertFalse(grader.audit_go_metadata(go_metadata(main=False))[0])

    def test_broken_metadata_is_an_infrastructure_error(self):
        with self.assertRaises(grader.GraderInfrastructureError):
            grader.audit_go_metadata({"root.json": b"bad"})

    def test_real_fixtures_validate(self):
        payload, answers, hashes = grader.load_fixtures(TASK / "tests")
        self.assertEqual(len(grader.lf_records(payload)), 2000)
        self.assertEqual(len(answers), 2000)
        self.assertEqual(len(hashes), 5)


class MockedEvaluationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.workspace = self.root / "repo"
        self.workspace.mkdir()
        self.tests = self.root / "tests"
        self.tests.mkdir()
        (self.tests / ".container-verifier").touch()
        self.patches = [
            patch.object(grader, "WORKSPACE", self.workspace),
            patch.object(grader, "TESTS", self.tests),
            patch.object(grader, "PRIVATE", self.root / "private"),
            patch.object(grader, "LOGS", self.root / "logs"),
            patch.object(grader.os, "geteuid", return_value=0),
            patch.object(grader, "load_fixtures", return_value=(b"a\nb\n", [b"A", b"B"], {})),
        ]
        for item in self.patches:
            item.start()
            self.addCleanup(item.stop)
        grader._CACHE.clear()
        self.addCleanup(grader._CACHE.clear)
        self.worker = Mock()
        self.mock_factory = patch.object(grader, "make_worker", return_value=self.worker)
        self.mock_factory.start()
        self.addCleanup(self.mock_factory.stop)

    def good_build(self):
        return WorkerResult(returncode=0, stdout=b"", stderr="", files=go_metadata())

    def test_one_build_and_one_execution_are_cached_for_all_scores(self):
        self.worker.run.side_effect = [self.good_build(), WorkerResult(0, b"A\nB\n", "")]
        for _ in range(3):
            self.assertEqual(grader.evaluate(self.workspace), {"build": 1, "no_python": 1, "behaviour": 1})
        self.assertEqual(self.worker.run.call_count, 2)
        build_call, execution_call = self.worker.run.call_args_list
        self.assertEqual(build_call.kwargs["files"], [self.workspace])
        self.assertEqual(execution_call.kwargs["stdin"], b"a\nb\n")
        self.assertEqual(len(execution_call.kwargs["files"]), 2)
        self.assertNotIn(self.tests, execution_call.kwargs["files"])

    def test_python_retention_gates_only_no_python(self):
        (self.workspace / "old.py").write_text("# source")
        self.worker.run.side_effect = [self.good_build(), WorkerResult(0, b"A\nB\n", "")]
        self.assertEqual(grader.evaluate(self.workspace), {"build": 1, "no_python": 0, "behaviour": 1})

    def test_failed_build_gates_no_python_and_behaviour(self):
        self.worker.run.return_value = WorkerResult(1, b"", "untrusted compile diagnostics")
        self.assertEqual(grader.evaluate(self.workspace), {"build": 0, "no_python": 0, "behaviour": 0})
        self.assertEqual(self.worker.run.call_count, 1)

    def test_submission_timeout_is_a_score_failure(self):
        self.worker.run.side_effect = WorkerError("timeout")
        self.assertEqual(grader.evaluate(self.workspace), {"build": 0, "no_python": 0, "behaviour": 0})

    def test_failed_execution_preserves_build_points(self):
        self.worker.run.side_effect = [self.good_build(), WorkerResult(2, b"A\nB\n", "")]
        self.assertEqual(grader.evaluate(self.workspace), {"build": 1, "no_python": 1, "behaviour": 0})

    def test_boundary_failure_propagates_without_reward(self):
        self.worker.run.side_effect = WorkerSetupError("mock boundary failure")
        with self.assertRaises(WorkerSetupError):
            grader.evaluate(self.workspace)
        self.assertFalse((self.root / "logs/reward.json").exists())
        details = json.loads((self.root / "logs/grade-details.json").read_text())
        self.assertEqual(details["infrastructure_error"], "WorkerSetupError")

    def test_report_does_not_include_candidate_or_hidden_text(self):
        self.worker.run.side_effect = [self.good_build(), WorkerResult(0, b"private-looking\ntext\n", "SECRET_MARKER")]
        grader.evaluate(self.workspace)
        report = (self.root / "logs/grade-details.json").read_text()
        self.assertNotIn("private-looking", report)
        self.assertNotIn("SECRET_MARKER", report)
        self.assertFalse((self.root / "private/candidate").exists())


class RewardKitIntegrationTests(unittest.TestCase):
    def test_discovery_keys_and_weighted_mean_without_workers(self):
        import rewardkit
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "reward.json"
            with patch.object(grader, "evaluate", return_value={"build": 1.0, "no_python": 0.0, "behaviour": 0.0}):
                result = rewardkit.run(TASK / "tests", workspace=TASK / "environment/repo", output=output,
                                       max_concurrent_programmatic=1)
            self.assertEqual(result, {"build": 1.0, "no_python": 0.0, "behaviour": 0.0, "reward": 0.1667})


if __name__ == "__main__":
    unittest.main(verbosity=2)

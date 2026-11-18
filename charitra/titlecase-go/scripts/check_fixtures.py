#!/usr/bin/env python3
"""Verify frozen fixture integrity, provenance, record counts and reproducibility.

Run: python3.12 -S scripts/check_fixtures.py
This authoring check does not run Harbor or report model performance.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile


def records(path: Path) -> list[bytes]:
    payload = path.read_bytes()
    if not payload.endswith(b"\n"):
        raise AssertionError(f"Missing final LF: {path.name}")
    values = payload[:-1].split(b"\n")
    if b"\r" in payload:
        raise AssertionError(f"CR present in LF-only fixture: {path.name}")
    for value in values:
        value.decode("utf-8", errors="strict")
    return values


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    data = root / "tests" / "data"
    manifest = json.loads((data / "manifest.json").read_text(encoding="utf-8"))
    spec = importlib.util.spec_from_file_location("_fixture_generator", root / "tests" / "gen.py")
    if spec is None or spec.loader is None:
        raise AssertionError("Cannot load fixture generator")
    sys.dont_write_bytecode = True
    gen = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gen)
    reference = gen.reference_module(root / "environment" / "repo")
    if sys.version_info[:2] != (3, 12):
        raise SystemExit("Run this check with Python 3.12 and -S")
    if manifest["upstream"]["commit"] != gen.UPSTREAM_SHA:
        raise AssertionError("Manifest does not identify the pinned upstream commit")
    if manifest["upstream"]["source_sha256"] != gen.SOURCE_SHA256:
        raise AssertionError("Manifest source hash does not match the generator")
    if manifest["reference"]["regex_backend"] != "stdlib re" or reference.REGEX_AVAILABLE:
        raise AssertionError("Wrong reference regex backend")
    all_records = {}
    for name, metadata in manifest["files"].items():
        path = data / name
        payload = path.read_bytes()
        rows = records(path)
        if len(rows) != 2000 or len(rows) != metadata["records"]:
            raise AssertionError(f"Incorrect record count: {name}")
        if len(payload) != metadata["bytes"] or hashlib.sha256(payload).hexdigest() != metadata["sha256"]:
            raise AssertionError(f"Frozen fixture was changed: {name}")
        if max(map(len, rows)) != metadata["max_record_bytes"] or rows.count(b"") != metadata["blank_records"]:
            raise AssertionError(f"Incorrect record metadata: {name}")
        all_records[name] = rows
    public = all_records["inputs.txt"]
    hidden = all_records["hidden_inputs.txt"]
    if len(set(public)) != 2000 or len(set(hidden)) != 2000 or set(public).intersection(hidden):
        raise AssertionError("Input sets must each be unique and mutually disjoint")
    if max(map(len, public)) < 80 * 1024 or max(map(len, hidden)) < 80 * 1024:
        raise AssertionError("Both corpora must exercise long lines")
    for input_name, expected_name in [("inputs.txt", "expected.txt"), ("hidden_inputs.txt", "hidden_expected.txt")]:
        for i, (given, expected) in enumerate(zip(all_records[input_name], all_records[expected_name], strict=True), 1):
            actual = reference.titlecase(given.decode("utf-8")).encode("utf-8")
            if actual != expected:
                raise AssertionError(f"Frozen answer disagrees with original Python: {input_name}:{i}")
    with tempfile.TemporaryDirectory(prefix="titlecase-fixture-check-") as temporary:
        outputs = [Path(temporary) / "first", Path(temporary) / "second"]
        for output in outputs:
            subprocess.run([sys.executable, "-S", str(root / "tests" / "gen.py"), "--output", str(output)], check=True, capture_output=True, text=True)
        for name in manifest["files"]:
            original = (data / name).read_bytes()
            if original != (outputs[0] / name).read_bytes() or original != (outputs[1] / name).read_bytes():
                raise AssertionError(f"Generation is not reproducible: {name}")
    replay_matches = sum(a == b for a, b in zip(all_records["expected.txt"], all_records["hidden_expected.txt"], strict=True))
    result = {"status": "passed", "check_kind": "authoring_fixture_validation_not_harbor", "records_per_file": 2000,
              "unique_public_inputs": len(set(public)), "unique_hidden_inputs": len(set(hidden)), "public_hidden_disjoint": True,
              "all_expected_answers_recomputed_from_original": True, "two_regenerations_byte_identical": True,
              "public_max_record_bytes": max(map(len, public)), "hidden_max_record_bytes": max(map(len, hidden)),
              "visible_answer_replay_matching_hidden_rows": replay_matches,
              "original_source_sha256": gen.SOURCE_SHA256, "upstream_commit": gen.UPSTREAM_SHA}
    payload = json.dumps(result, indent=2) + "\n"
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(payload, encoding="utf-8", newline="\n")
    print(payload, end="")


if __name__ == "__main__":
    main()

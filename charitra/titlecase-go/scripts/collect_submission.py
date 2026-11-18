#!/usr/bin/env python3
"""Collect submission files only from validated, actual Harbor Docker trials."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil

from verify_evidence import verify


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_directory", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    root = args.run_directory.resolve()
    task_root = Path(__file__).resolve().parent.parent
    destination = (args.output or task_root / "evidence/submission").resolve()
    if destination.exists():
        raise SystemExit(f"Choose a new --output directory; already exists: {destination}")

    # This validates completed trials, real reward files, weights, isolation
    # metadata and all three required thresholds before any submission is made.
    summary = verify(root)
    destination.mkdir(parents=True)
    (destination / "screenshots").mkdir()
    for filename in ("run-manifest.json", "evidence-summary.json", "preflight.txt"):
        shutil.copy2(root / filename, destination / filename)
    rows = []
    for label in ("oracle", "nop", "cheat"):
        item = summary["jobs"][label]
        trial = root / item["trial_result"]
        target = destination / label
        target.mkdir()
        shutil.copy2(trial, target / "trial-result.json")
        shutil.copy2(trial.parent / "verifier/reward.json", target / "reward.json")
        shutil.copy2(trial.parent / "verifier/grade-details.json", target / "grade-details.json")
        scores = item["scores"]
        rows.append("| " + " | ".join([label] + [str(scores[k]) for k in
                    ("build", "no_python", "behaviour", "reward")]) + " |")

    content = "\n".join([
        "# Actual Harbor validation results", "",
        "These values were read from completed Harbor Docker trials and checked",
        "by `scripts/verify_evidence.py`; they are not predictions or local mocks.", "",
        f"Validated at: {summary['validated_at']}", "",
        "| Control | Build | No Python | Behaviour | Reward |",
        "| --- | ---: | ---: | ---: | ---: |", *rows, "",
        "## Screenshots still to capture", "",
        "Open the actual trials in `harbor view` and save the corresponding images",
        "under `screenshots/oracle.png`, `screenshots/nop.png`, and `screenshots/cheat.png`.",
        "After adding them, update this heading to confirm they are present.", "",
        "## Reflection", "",
        "Add `REFLECTION.md` with two truthful lines: the implementation rules that",
        "actually required fixes (or state that no mismatch history was recorded),",
        "and one fair hardening idea. Do not invent a history of failures.", "",
    ])
    (destination / "RESULTS.md").write_text(content, encoding="utf-8")
    print(json.dumps({"status": "collected_actual_harbor_evidence", "output": str(destination),
                      "screenshots": "capture from actual viewer", "reflection": "write from actual work"}, indent=2))


if __name__ == "__main__":
    main()

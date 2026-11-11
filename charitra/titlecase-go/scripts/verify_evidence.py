#!/usr/bin/env python3
"""Check actual Harbor trial artifacts; zero scores never stand in for errors."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
from typing import Any

SCORE_KEYS = {"build", "no_python", "behaviour", "reward"}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def read_trial(job: Path) -> tuple[Path, dict[str, Any]]:
    found = []
    for path in sorted(job.glob("*/result.json")):
        value = json.loads(path.read_text())
        if "trial_name" in value and "task_name" in value:
            found.append((path, value))
    require(len(found) == 1, f"{job}: expected one real completed trial, found {len(found)}")
    path, trial = found[0]
    require(trial.get("exception_info") is None, f"{path}: trial has an infrastructure/agent exception")
    require(bool(trial.get("started_at") and trial.get("finished_at")), f"{path}: trial is not complete")
    require(trial.get("verifier_environment_mode") == "separate", f"{path}: verifier was not separate")
    environment = trial.get("config", {}).get("environment", {})
    require(environment.get("type") == "docker", f"{path}: trial did not use Docker")
    require(environment.get("kwargs", {}).get("auto_mounting") is False,
            f"{path}: auto_mounting=false was not recorded")
    return path, trial


def validate_scores(label: str, scores: Any) -> dict[str, float]:
    require(isinstance(scores, dict) and set(scores) == SCORE_KEYS,
            f"{label}: reward JSON must contain exactly {sorted(SCORE_KEYS)}")
    for name, value in scores.items():
        require(type(value) in (int, float) and math.isfinite(value) and 0 <= value <= 1,
                f"{label}: {name} is not a finite score in [0,1]")
    wanted = (scores["build"] + scores["no_python"] + 4 * scores["behaviour"]) / 6
    require(abs(scores["reward"] - wanted) <= 0.00011, f"{label}: incorrect 1:1:4 aggregate")
    if label == "oracle":
        require(all(value == 1 for value in scores.values()), f"oracle must score 1 in every dimension: {scores}")
    elif label == "nop":
        require(all(value == 0 for value in scores.values()), f"nop must score 0 in every dimension: {scores}")
    elif label == "cheat":
        require(scores["build"] == 1 and scores["no_python"] == 0,
                f"cheat control must build and retain Python files: {scores}")
        require(scores["reward"] < 0.2, f"replay cheat must score below 0.2: {scores}")
    return scores


def verify(root: Path) -> dict[str, Any]:
    manifest_path = root / "run-manifest.json"
    manifest = json.loads(manifest_path.read_text())
    results = {}
    for label, relative_job in manifest["jobs"].items():
        require(label in {"oracle", "nop", "cheat"}, f"Unexpected job {label}")
        path, trial = read_trial(root / relative_job)
        agent = trial.get("agent_info", {}).get("name")
        require(agent == ("nop" if label == "nop" else "oracle"), f"{label}: wrong agent: {agent}")
        rewards_path = path.parent / "verifier/reward.json"
        scores = validate_scores(label, json.loads(rewards_path.read_text()))
        require(trial.get("verifier_result", {}).get("rewards") == scores,
                f"{label}: trial result and verifier reward file disagree")
        details_path = path.parent / "verifier/grade-details.json"
        details = json.loads(details_path.read_text())
        require("infrastructure_error" not in details, f"{label}: verifier infrastructure failed")
        require(details.get("hidden_records") == 2000, f"{label}: hidden fixture count differs")
        require(details.get("isolation") == "rewardkit.Worker/fresh-uid", f"{label}: no Worker evidence")
        require(details.get("scores") is not None, f"{label}: grader details are missing")
        for key in ("build", "no_python", "behaviour"):
            require(abs(details["scores"][key] - scores[key]) <= 0.000051,
                    f"{label}: {key} differs between grader and RewardKit")
        if label == "oracle":
            require(details.get("matched_records") == 2000 and details.get("output_records") == 2000,
                    "oracle: expected exactly 2000 matching records")
        results[label] = {
            "trial_name": trial["trial_name"],
            "trial_result": str(path.relative_to(root)),
            "trial_result_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "reward_json": str(rewards_path.relative_to(root)),
            "scores": scores,
            "matched_records": details.get("matched_records"),
            "output_records": details.get("output_records"),
            "build_status": details.get("build_status"),
            "behaviour_status": details.get("behaviour_status"),
            "started_at": trial["started_at"],
            "finished_at": trial["finished_at"],
        }
    require(set(results) == {"oracle", "nop", "cheat"}, "All three controls must be present")
    summary = {
        "schema_version": 1,
        "status": "passed",
        "proof_type": "real Harbor Docker trial artifacts",
        "validated_at": datetime.now(timezone.utc).isoformat(),
        "jobs": results,
        "requirements": {"oracle": "all four scores equal 1", "nop": "all four scores equal 0",
                         "cheat": "build=1; no_python=0; reward<0.2"},
    }
    (root / "evidence-summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    manifest["status"] = "passed"
    manifest["validated_at"] = summary["validated_at"]
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_directory", type=Path)
    args = parser.parse_args()
    result = verify(args.run_directory.resolve())
    print(json.dumps({label: item["scores"] for label, item in result["jobs"].items()}, indent=2))


if __name__ == "__main__":
    main()

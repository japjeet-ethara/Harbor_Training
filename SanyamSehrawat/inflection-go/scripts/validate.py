#!/usr/bin/env python3
"""Validate the task through Harbor. Needs Docker running and `harbor` on PATH.

    python scripts/validate.py [jobs_dir]

Runs three trials and checks their rewards:

    oracle  the reference solution               must score 1.0
    nop     an agent that does nothing           must score 0.0
    cheat   prints the VISIBLE answer sheet      must score below 0.2

The cheat runs on a throw-away copy of the task whose solution/ is cheat/solve.sh
plus tests/data/expected.txt, so the real solution is never touched.
Exits 0 only if all three pass. Job folders go to jobs_dir (default: a new
temporary folder), with a time stamp in their names.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

TASK = Path(__file__).resolve().parent.parent
STAMP = time.strftime("%Y%m%d-%H%M%S")


def harbor_run(task_dir, agent, jobs, label):
    name = f"{label}-{STAMP}"
    env = {**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"}
    done = subprocess.run(
        ["harbor", "run", "-p", str(task_dir), "-a", agent, "-o", str(jobs), "--job-name", name],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )
    rewards = sorted((jobs / name).glob("*/verifier/reward.json"))
    if done.returncode != 0 or len(rewards) != 1:
        tail = done.stderr.decode("utf-8", "replace")[-800:]
        sys.exit(f"{label}: harbor did not produce exactly one reward (exit {done.returncode})\n{tail}")
    return json.loads(rewards[0].read_text(encoding="utf-8"))


def main():
    if shutil.which("harbor") is None:
        sys.exit("harbor is not on PATH")
    jobs = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(tempfile.mkdtemp(prefix="inflection-go-jobs-"))
    jobs.mkdir(parents=True, exist_ok=True)

    results = {
        "oracle": harbor_run(TASK, "oracle", jobs, "oracle"),
        "nop": harbor_run(TASK, "nop", jobs, "nop"),
    }
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        copy = Path(tmp) / "inflection-go-cheat"
        shutil.copytree(TASK, copy, ignore=shutil.ignore_patterns(".git", "__pycache__"))
        shutil.rmtree(copy / "solution")
        (copy / "solution").mkdir()
        shutil.copyfile(TASK / "cheat" / "solve.sh", copy / "solution" / "solve.sh")
        shutil.copyfile(TASK / "tests" / "data" / "expected.txt", copy / "solution" / "expected.txt")
        results["cheat"] = harbor_run(copy, "oracle", jobs, "cheat")

    passed = {
        "oracle": results["oracle"]["reward"] == 1.0,
        "nop": results["nop"]["reward"] == 0.0,
        # build == 1.0 proves the cheat program really ran, so its low score is
        # earned by the hidden lines and not by a broken cheat.
        "cheat": results["cheat"]["reward"] < 0.2 and results["cheat"]["build"] == 1.0,
    }
    for label, reward in results.items():
        print(f"{'PASS' if passed[label] else 'FAIL'}  {label:<7} {json.dumps(reward, sort_keys=True)}")
    print(f"job folders: {jobs}")
    sys.exit(0 if all(passed.values()) else 1)


if __name__ == "__main__":
    main()

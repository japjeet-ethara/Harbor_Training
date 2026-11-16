#!/usr/bin/env python3
"""Run the three proof trials through Harbor and check their rewards.

    python scripts/validate.py [--jobs-dir DIR] [--only oracle,nop,cheat]

    oracle   solution/solve.sh, the reference Go port      must score 1.0
    nop      an agent that does nothing                    must score 0.0
    cheat    cheat/solve.sh, prints the SAMPLE answers     must score below 0.2

The cheat is run on a throw-away copy of the task whose solution/ folder holds
cheat/solve.sh and tests/data/sample/answers.txt; the real solution is never touched.
Needs Docker running and `harbor` installed (uv tool install harbor).
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

TASK = Path(__file__).resolve().parent.parent

LIMITS = {
    "oracle": lambda r: r == 1.0,
    "nop": lambda r: r == 0.0,
    "cheat": lambda r: r < 0.2,
}
WANTED = {"oracle": "= 1.0", "nop": "= 0.0", "cheat": "< 0.2"}


def harbor_executable():
    found = shutil.which("harbor")
    if found:
        return found
    for name in ("harbor.exe", "harbor"):
        candidate = Path.home() / ".local" / "bin" / name
        if candidate.exists():
            return str(candidate)
    sys.exit("harbor was not found on PATH or in ~/.local/bin")


def run_trial(harbor, task_dir, agent, jobs_dir, job_name):
    cmd = [harbor, "run", "-p", str(task_dir), "-a", agent, "-o", str(jobs_dir), "--job-name", job_name]
    print("+", " ".join(cmd), flush=True)
    subprocess.run(cmd, check=False)
    rewards = list((jobs_dir / job_name).glob("*/verifier/reward.json"))
    if not rewards:
        return None
    return json.loads(rewards[0].read_text())


def cheat_copy(stamp):
    copy = TASK.parent / f"{TASK.name}-cheat-{stamp}"
    shutil.copytree(TASK, copy, ignore=shutil.ignore_patterns(".git", "screenshots", "__pycache__"))
    shutil.rmtree(copy / "solution")
    (copy / "solution").mkdir()
    shutil.copy(TASK / "cheat" / "solve.sh", copy / "solution" / "solve.sh")
    shutil.copy(TASK / "tests" / "data" / "sample" / "answers.txt", copy / "solution" / "answers.txt")
    return copy


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--jobs-dir", default=str(TASK.parent / "runs"))
    parser.add_argument("--only", default="oracle,nop,cheat")
    args = parser.parse_args()

    harbor = harbor_executable()
    jobs_dir = Path(args.jobs_dir).resolve()
    jobs_dir.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    results = {}

    for trial in args.only.split(","):
        job_name = f"{trial}-{stamp}"
        if trial == "oracle":
            results[trial] = run_trial(harbor, TASK, "oracle", jobs_dir, job_name)
        elif trial == "nop":
            results[trial] = run_trial(harbor, TASK, "nop", jobs_dir, job_name)
        elif trial == "cheat":
            copy = cheat_copy(stamp)
            try:
                results[trial] = run_trial(harbor, copy, "oracle", jobs_dir, job_name)
            finally:
                shutil.rmtree(copy, ignore_errors=True)
        else:
            sys.exit(f"unknown trial {trial!r}")

    print()
    print(f"{'trial':<8}{'build':>7}{'no_py':>7}{'behav':>7}{'reward':>8}  wanted  ok")
    all_ok = True
    for trial, reward in results.items():
        if reward is None:
            print(f"{trial:<8}{'no reward.json written':>29}  {WANTED[trial]:<7} NO")
            all_ok = False
            continue
        ok = LIMITS[trial](reward["reward"])
        all_ok &= ok
        print(f"{trial:<8}{reward['build']:>7}{reward['no_python']:>7}{reward['behaviour']:>7}"
              f"{reward['reward']:>8}  {WANTED[trial]:<7} {'yes' if ok else 'NO'}")
    print(f"\njobs written to {jobs_dir}")
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()

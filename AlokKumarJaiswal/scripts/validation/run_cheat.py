# -*- coding: utf-8 -*-
"""Swap in one cheat solve.sh, run the oracle, then restore the real script."""

import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOLVE_PATH = ROOT / "titlecase-go" / "solution" / "solve.sh"
BACKUP_PATH = ROOT / "solution_backup" / "solve.sh.real"
CHEAT_DIR = ROOT / "cheat"
TASK_DIR = ROOT / "titlecase-go"

REAL_SHA = "81e0830780473724c8a484d3c2f68d2b7e876caf1102f8dd29ce24a508a62fc0"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_utf8_bytes(path: Path) -> bytes:
    data = path.read_bytes()
    data.decode("utf-8")
    return data


def read_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def abort(message: str) -> None:
    print(message, file=sys.stderr)
    sys.exit(1)


def restore() -> bool:
    try:
        shutil.copyfile(BACKUP_PATH, SOLVE_PATH)
        data = read_utf8_bytes(SOLVE_PATH)
        digest = sha256_bytes(data)
    except (OSError, UnicodeError) as exc:
        print(f"ERROR: restore failed: {exc}", file=sys.stderr)
        return False
    if digest != REAL_SHA:
        print(
            f"ERROR: restored solve.sh sha256 {digest} != {REAL_SHA}",
            file=sys.stderr,
        )
        return False
    print("restored OK")
    return True


def trials_for_job(job_dir: Path) -> list[str]:
    result_path = job_dir / "result.json"
    if not result_path.is_file():
        abort(f"ERROR: no result.json under {job_dir}")
    job = read_json(result_path)
    names: list[str] = []
    evals = job.get("stats", {}).get("evals", {})
    for evaluation in evals.values():
        buckets = evaluation.get("reward_stats", {}).get("reward", {})
        for trial_names in buckets.values():
            names.extend(trial_names)
    seen: list[str] = []
    for trial_name in names:
        if trial_name not in seen:
            seen.append(trial_name)
    if not seen:
        abort(f"ERROR: no trial recorded for {job_dir}")
    return seen


def print_rewards(name: str) -> None:
    job_dir = ROOT / "jobs" / f"cheat-{name}"
    printed = False
    for trial_name in trials_for_job(job_dir):
        if "/" in trial_name or "\\" in trial_name or trial_name in {".", ".."}:
            abort(f"ERROR: trial name {trial_name!r} is not a folder of {job_dir}")
        trial_dir = job_dir / trial_name
        if trial_dir.parent != job_dir:
            abort(f"ERROR: trial {trial_name} is outside {job_dir}")
        reward_path = trial_dir / "verifier" / "reward.json"
        details_path = trial_dir / "verifier" / "reward-details.json"
        if not reward_path.is_file():
            abort(f"ERROR: no reward.json for trial {trial_name} under {job_dir}")
        reward = read_json(reward_path)
        details = read_json(details_path)
        scores = {
            component["name"]: component["detail"]["score"]
            for component in details["reward"]["components"]
        }
        print(
            f"{trial_dir.name} behaviour={scores['behaviour']} "
            f"build={scores['build']} no_python={scores['no_python']} "
            f"reward={reward['reward']}"
        )
        printed = True
    if not printed:
        abort(f"ERROR: no reward.json for this job under {job_dir}")


def main() -> None:
    if not TASK_DIR.is_dir():
        abort(f"abort: missing {TASK_DIR}")
    if not SOLVE_PATH.is_file():
        abort(f"abort: missing {SOLVE_PATH}")
    if not CHEAT_DIR.is_dir():
        abort(f"abort: missing {CHEAT_DIR}")

    allowed = {path.stem for path in CHEAT_DIR.glob("*.sh")}
    if len(sys.argv) != 2 or sys.argv[1] not in allowed:
        abort("usage: run_cheat.py NAME")

    name = sys.argv[1]
    cheat_path = CHEAT_DIR / f"{name}.sh"
    if not cheat_path.is_file():
        abort(f"abort: missing {cheat_path}")

    real = read_utf8_bytes(SOLVE_PATH)
    actual = sha256_bytes(real)
    if actual != REAL_SHA:
        abort(f"abort: sha256 {actual} != {REAL_SHA}")

    job_dir = ROOT / "jobs" / f"cheat-{name}"
    if job_dir.exists():
        abort(f"abort: {job_dir} already exists; nothing was modified")

    read_utf8_bytes(cheat_path)
    BACKUP_PATH.parent.mkdir(parents=True, exist_ok=True)

    return_code = 1
    backed_up = False
    try:
        shutil.copyfile(SOLVE_PATH, BACKUP_PATH)
        backup = read_utf8_bytes(BACKUP_PATH)
        if sha256_bytes(backup) != REAL_SHA:
            abort(f"abort: backup sha256 != {REAL_SHA}")
        backed_up = True
        shutil.copyfile(cheat_path, SOLVE_PATH)
        completed = subprocess.run(
            [
                "harbor",
                "run",
                "-p",
                str(TASK_DIR),
                "-a",
                "oracle",
                "--job-name",
                f"cheat-{name}",
            ],
            cwd=ROOT,
        )
        return_code = completed.returncode
    finally:
        restored = restore() if backed_up else False

    if not backed_up:
        sys.exit(1)
    if not restored:
        sys.exit(1)

    if return_code != 0:
        print("HARBOR FAILED, no results read")
        sys.exit(return_code)

    print_rewards(name)


if __name__ == "__main__":
    main()

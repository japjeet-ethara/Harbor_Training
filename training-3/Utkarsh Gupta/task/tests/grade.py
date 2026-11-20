#!/usr/bin/env python3
"""Verifier: three weighted checks -> /logs/verifier/reward.json (weighted-mean)."""
import json
import subprocess
from pathlib import Path

REPO = Path("/workspace/repo")
DATA = Path(__file__).resolve().parent / "data"
OUT = Path("/logs/verifier")
BIN = Path("/tmp/titlecase_bin")
WEIGHTS = {"build": 1.0, "no_python": 1.0, "behaviour": 4.0}


def run(cmd, **kw):
    return subprocess.run(cmd, cwd=REPO, capture_output=True, **kw)


def check_build() -> bool:
    try:
        return run(["go", "build", "./..."], timeout=300).returncode == 0
    except Exception:
        return False


def check_no_python(build_ok: bool) -> bool:
    # pays only when the build passes, so deleting files alone earns nothing
    return build_ok and not any(REPO.rglob("*.py"))


def check_behaviour(build_ok: bool) -> float:
    if not build_ok:
        return 0.0
    try:
        if run(["go", "build", "-o", str(BIN), "."], timeout=300).returncode != 0:
            return 0.0
        inputs = (DATA / "hidden_inputs.txt").read_bytes()
        expected = (DATA / "hidden_expected.txt").read_bytes().split(b"\n")
        if expected and expected[-1] == b"":
            expected.pop()
        proc = subprocess.run([str(BIN)], input=inputs, capture_output=True, timeout=300)
        got = proc.stdout.split(b"\n")
        if got and got[-1] == b"":
            got.pop()
        total = max(len(expected), len(got))
        if total == 0:
            return 0.0
        same = sum(1 for a, b in zip(expected, got) if a == b)
        return same / total
    except Exception:
        return 0.0


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    build_ok = check_build()
    scores = {
        "build": 1.0 if build_ok else 0.0,
        "no_python": 1.0 if check_no_python(build_ok) else 0.0,
        "behaviour": check_behaviour(build_ok),
    }
    scores["reward"] = sum(scores[k] * w for k, w in WEIGHTS.items()) / sum(WEIGHTS.values())
    (OUT / "reward.json").write_text(json.dumps(scores, indent=2))
    print(json.dumps(scores, indent=2))


if __name__ == "__main__":
    main()

import argparse
from contextlib import ExitStack
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from unittest.mock import patch

from reference import ROOT, SOURCE

sys.path.insert(0, str(ROOT / "tests"))
import evaluator


def native_run(command, workspace, scratch, timeout, data=None):
    command = list(command)
    env = dict(os.environ, **evaluator.candidate_environment(scratch))
    env["TMP"] = env["TEMP"] = str(scratch)
    env["PATH"] = str(Path(evaluator.GO).parent) + os.pathsep + os.environ.get("PATH", "")
    if os.name == "nt":
        if "-o" in command:
            index = command.index("-o") + 1
            command[index] += ".exe"
        if command[0] == str(scratch / "titlecase"):
            command[0] += ".exe"
    try:
        result = subprocess.run(
            command, input=data if data is not None else b"", capture_output=True,
            timeout=timeout, cwd=workspace, env=env, check=False,
        )
    except subprocess.TimeoutExpired:
        return None
    if result.returncode != 0:
        print(f"local subprocess exit {result.returncode}: {result.stderr[:700]!r}", file=sys.stderr)
        return None
    return result.stdout


def check_framing():
    compare = evaluator.compare
    expected = b"Alpha\n\nOmega\n"
    samples = {
        expected: 1,
        b"Alpha\n\nWrong\n": 2 / 3,
        b"alpha\n\nOmega\n": 2 / 3,
        b"Alpha\r\n\nOmega\n": 2 / 3,
        b"Alpha\n\nOmega": 0,
        b"Alpha\n\nOmega\n\n": 0,
        b"Alpha\n": 0,
        b"": 0,
    }
    for actual, score in samples.items():
        assert compare(actual, expected) == score
    print(f"grader framing: {len(samples)} cases passed")


def install_go(workspace, scenario):
    solution = ROOT / "solution" / "src"
    if scenario == "oracle":
        for path in solution.iterdir():
            shutil.copyfile(path, workspace / path.name)
        for path in workspace.rglob("*.py"):
            path.unlink()
    elif scenario == "replay":
        script = (ROOT / "cheat" / "solve.sh").read_text(encoding="utf-8")
        parts = script.split("<<'EOF'\n")
        for name, part in zip(("go.mod", "main.go"), parts[1:], strict=True):
            (workspace / name).write_bytes(part.split("\nEOF", 1)[0].encode() + b"\n")
        shutil.copyfile(ROOT / "tests" / "data" / "expected.txt", workspace / "visible-answers.txt")
        (workspace / "only-nested").mkdir()
        for path in list(workspace.rglob("*.py")):
            path.unlink()
        (workspace / "only-nested" / "leftover.py").touch()
    elif scenario == "broken":
        (workspace / "go.mod").write_text("module invalid.local/broken\n\ngo 1.23.0\n")
        (workspace / "main.go").write_text("package main\ninvalid go code!\n")
        for path in workspace.rglob("*.py"):
            path.unlink()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--go", type=Path, required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--rewardkit", action="store_true")
    args = parser.parse_args()
    args.evidence.mkdir(parents=True, exist_ok=False)
    check_framing()
    go = str(args.go.resolve(strict=True))
    version = subprocess.check_output([go, "version"], text=True).strip()
    print(f"Profile: native subprocesses, no Docker or Linux UID isolation; {version}")
    scenarios = {
        "nop": evaluator.Result(),
        "broken": evaluator.Result(),
        "oracle": evaluator.Result(True, True, 1.0),
        "replay": evaluator.Result(True, False, 0.0),
    }
    report = {}
    with tempfile.TemporaryDirectory(prefix="titlecase-native-") as tmp, ExitStack() as stack:
        temp = Path(tmp)
        stack.enter_context(patch.object(evaluator, "GO", go))
        stack.enter_context(patch.object(evaluator, "prepare_workspace", lambda *_: None))
        stack.enter_context(patch.object(evaluator, "run", native_run))
        if args.rewardkit:
            from rewardkit import run
            checks = temp / "tests"
            checks.mkdir()
            shutil.copyfile(ROOT / "tests" / "reward.toml", checks / "reward.toml")
            for name in ("build", "no_python", "behaviour"):
                shutil.copytree(ROOT / "tests" / name, checks / name)
        for label, expected in scenarios.items():
            workspace = temp / label
            shutil.copytree(SOURCE, workspace)
            install_go(workspace, label)
            results = evaluator.evaluate(workspace)
            assert results == expected, (label, results, expected)
            values = {
                "build": float(results.build), "no_python": float(results.no_python),
                "behaviour": results.behaviour,
            }
            reward = (values["build"] + values["no_python"] + 4 * values["behaviour"]) / 6
            report[label] = values | {"reward": reward}
            if args.rewardkit:
                output = args.evidence / label
                output.mkdir()
                scores = run(checks, workspace=workspace, output=output / "reward.json",
                             max_concurrent_programmatic=1)
                assert scores.keys() == values.keys() | {"reward"}
                assert all(math.isclose(scores[key], value) for key, value in values.items())
                assert scores["reward"] == round(reward, 4)
                report[label]["rewardkit_reward"] = scores["reward"]
            print(label, json.dumps(report[label]), flush=True)
    (args.evidence / "results.json").write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()

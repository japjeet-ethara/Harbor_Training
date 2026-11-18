#!/usr/bin/env python3
"""Score the agent's repository and write the reward file.

    python3 grade.py <repo> <data dir with titles.txt + answers.txt> <reward.json>

Three checks, combined as a weighted mean:

    build      weight 1   `go build ./...` and `go build -o /tmp/titlecase .` succeed,
                          go.mod has no require/replace directive
    no_python  weight 1   build passed and no *.py file is left under the repo
    behaviour  weight 4   share of graded titles whose output line is byte-identical
                          to the frozen answer (0 when the build failed)

The reward file is written on every code path, including crashes, so a broken grader
scores 0 instead of leaving the trial without a reward.
"""

import json
import os
import re
import subprocess
import sys
import traceback

WEIGHTS = {"build": 1, "no_python": 1, "behaviour": 4}
BINARY = "/tmp/titlecase"
GO_ENV = {
    "GOTOOLCHAIN": "local",
    "GOPROXY": "off",
    "GOFLAGS": "-mod=mod",
    "CGO_ENABLED": "0",
    "GOCACHE": "/tmp/gocache",
    "HOME": "/tmp",
}


def run(cmd, cwd=None, timeout=300, stdin=None):
    env = dict(os.environ, **GO_ENV)
    return subprocess.run(cmd, cwd=cwd, env=env, stdin=stdin, capture_output=True, timeout=timeout)


def check_build(repo):
    go_mod = os.path.join(repo, "go.mod")
    if not os.path.isfile(go_mod):
        print("build: go.mod is missing")
        return 0.0
    with open(go_mod, encoding="utf-8", errors="replace") as f:
        text = f.read()
    if re.search(r"^\s*(require|replace)\b", text, re.M):
        print("build: go.mod has a require or replace directive")
        return 0.0
    for cmd in (["go", "build", "./..."], ["go", "build", "-o", BINARY, "."]):
        result = run(cmd, cwd=repo)
        if result.returncode != 0:
            print("build:", " ".join(cmd), "failed")
            print(result.stderr.decode(errors="replace"))
            return 0.0
    print("build: ok")
    return 1.0


def check_no_python(repo):
    leftovers = []
    for root, _dirs, files in os.walk(repo):
        leftovers += [os.path.join(root, f) for f in files if f.endswith(".py")]
    if leftovers:
        print("no_python: %d .py file(s) remain, e.g. %s" % (len(leftovers), leftovers[0]))
        return 0.0
    print("no_python: ok")
    return 1.0


def kill_processes_of(user):
    import pwd
    import signal

    uid = pwd.getpwnam(user).pw_uid
    for pid in os.listdir("/proc"):
        if pid.isdigit():
            try:
                if os.stat("/proc/" + pid).st_uid == uid:
                    os.kill(int(pid), signal.SIGKILL)
            except OSError:
                pass


def check_behaviour(data_dir):
    with open(os.path.join(data_dir, "titles.txt"), "rb") as f:
        titles = f.read()
    with open(os.path.join(data_dir, "answers.txt"), "rb") as f:
        answers = f.read().split(b"\n")[:-1]

    # The program runs as `nobody`: it must not be able to read this folder, which holds
    # the answers. It only gets the titles through its standard input.
    os.chmod(os.path.dirname(os.path.abspath(__file__)), 0o700)
    os.chmod(BINARY, 0o755)
    try:
        result = subprocess.run(
            ["runuser", "-u", "nobody", "--", BINARY],
            input=titles, capture_output=True, timeout=120, cwd="/tmp",
        )
    except subprocess.TimeoutExpired:
        print("behaviour: the program did not finish within 120 s")
        return 0.0
    finally:
        kill_processes_of("nobody")  # nothing the program started may outlive the grader
    if result.returncode != 0:
        print("behaviour: exit status %d" % result.returncode)
        print(result.stderr.decode(errors="replace")[:2000])
    produced = result.stdout.split(b"\n")
    if produced and produced[-1] == b"":
        produced = produced[:-1]
    matched = sum(1 for i, want in enumerate(answers) if i < len(produced) and produced[i] == want)
    print("behaviour: %d of %d lines match (%d lines produced)" % (matched, len(answers), len(produced)))
    for i, want in enumerate(answers):
        got = produced[i] if i < len(produced) else b"<missing>"
        if got != want:
            print("  first mismatch, line %d: expected %r, got %r" % (i + 1, want, got))
            break
    return matched / len(answers)


def grade(repo, data_dir):
    scores = {"build": 0.0, "no_python": 0.0, "behaviour": 0.0}
    scores["build"] = check_build(repo)
    if scores["build"] == 1.0:
        scores["no_python"] = check_no_python(repo)
        scores["behaviour"] = check_behaviour(data_dir)
    return scores


def main():
    repo, data_dir, reward_path = sys.argv[1:4]
    scores = {"build": 0.0, "no_python": 0.0, "behaviour": 0.0}
    try:
        scores = grade(repo, data_dir)
    except Exception:
        traceback.print_exc()
    total = sum(WEIGHTS[k] * scores[k] for k in WEIGHTS) / sum(WEIGHTS.values())
    reward = {k: round(scores[k], 4) for k in WEIGHTS}
    reward["reward"] = round(total, 4)
    os.makedirs(os.path.dirname(reward_path), exist_ok=True)
    with open(reward_path, "w") as f:
        json.dump(reward, f, indent=2)
    print(json.dumps(reward))


if __name__ == "__main__":
    main()

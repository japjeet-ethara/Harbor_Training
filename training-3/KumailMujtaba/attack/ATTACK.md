# Attack report: Shubh Shukla's `titlecase-go` task

Attacker: Kumail Mujtaba
Target: `japjeet-ethara/Harbor_Training`, folder `ShubhShukla/titlecase-go`, commit `c5aee5eebd164c518d78de3c15eaae5975da7604` (see `TARGET.txt`).
Shubh had no `training-3/ShubhShukla/task/` yet, so I used his practice-1 folder, as the Day 4 instructions say. That folder has the same git tree (`a48a4ba`) on `main` and on `training-3`.
Harbor: 0.26.0. Every cheat ran as `harbor run -p <scratch copy> -a oracle`. In each scratch copy, `solution/` held only the cheat's `solve.sh`. `tests/`, `task.toml` and `environment/` were byte-identical to the target (checked with `diff -r`).

All `file:line` references are paths inside the target task folder.

## Baseline (sanity check, not a cheat)

Shubh's own oracle on my unmodified copy: **reward 1.0** (behavior 1, build 1, no_python 1). Job folder: `jobs/2026-11-19__14-22-04`.
The exam works on my machine, so the cheat scores below are meaningful.

Note for anyone re-running this on Windows: Git for Windows ships `core.autocrlf=true`. That turns the datasets and `test.sh` into CRLF and corrupts the exam. I checked out with `core.autocrlf=false` and confirmed that all four dataset sha256 hashes match `tests/datasets/manifest.json`.

## Step 4.1 — Reading the task as an attacker

I opened and checked every file and line quoted below.

**(1) What the agent can see inside the container**
- `environment/Dockerfile:1`: `FROM golang:1.23` (Debian bookworm, with `go`, `curl` and `git`).
- `environment/Dockerfile:3`: `COPY python-titlecase/ /workspace/repo/`. This copies only the Python library: `titlecase/__init__.py`, `titlecase/tests.py`, `setup.py`, `setup.cfg`, `pyproject.toml`, `tox.ini`, `README.rst`, `AUTHORS.rst`, `LICENSE.txt` and `.github/`.
- `environment/Dockerfile:5`: work dir `/workspace/repo`.
- No dataset, answer file or test script is copied into this image.
- `task.toml:25`: `network_mode = "public"`, so the agent also has the internet.

**(2) What `tests/test.sh` checks and how each check is scored**
- `tests/test.sh:4`: `python3 -m rewardkit /tests --workspace /workspace/repo --output /logs/verifier/reward.json`. It runs every `@criterion` in `tests/*.py`.
- `tests/reward.toml:4`: `weights = { build = 1.0, no_python = 1.0, behavior = 4.0 }`. The reward is (build + no_python + 4·behavior) / 6.
- `build`, `tests/build.py:12-23`: pass if `cd repo && go build ./...` exits 0 (`tests/grader_support.py:34-36`).
- `no_python`, `tests/no_python.py:12-26`: pass if no path name ends in `.py`, there are no symlinks (`tests/grader_support.py:44-52`), and the module builds.
- `behavior`, `tests/behavior.py:31-35`: builds to `titlecase-bin` and pipes in all of `hidden_input.txt` (`tests/grader_support.py:39-41`).
  It passes only if the exit code is 0 and the whole stdout equals `hidden_expected.txt` byte for byte (`tests/behavior.py:28`, `tests/grader_support.py:61-62`). All or nothing.
- Every check runs the submission through `rewardkit.Worker(env=GO_ENV)`: a fresh unprivileged UID, with `/tests` made private (`0700 root`).
  `GO_ENV` (`tests/grader_support.py:8-16`) sets `PATH=/usr/local/go/bin:/usr/local/bin:/usr/bin:/bin`, `GOPROXY=off` and `-mod=readonly`.

**(3) Which inputs the tests use and where they are stored**
- `behavior` uses only `HIDDEN_INPUT` / `HIDDEN_EXPECTED` (`tests/behavior.py:10-11,35`).
  These are `/tests/datasets/hidden_input.txt` and `hidden_expected.txt` (`tests/grader_support.py:18,21-22`): 2,000 fixed titles each, seed 1 (`tests/datasets/manifest.json:2,16`).
- `visible_input.txt` / `visible_expected.txt` are defined at `tests/grader_support.py:19-20`, but no criterion uses them.
- Visible and hidden titles share 0 lines (I checked with `comm`).
- All four files are committed to the public GitHub repo with the rest of `tests/`.

**(4) Is `tests/` visible to the agent while it works?**
- No, not on disk. `task.toml:16` sets `environment_mode = "separate"`. `tests/` is only copied into the separate verifier image (`tests/Dockerfile:12`, `COPY . /tests/`).
  Cheat 3 step A confirmed this: `absent: /tests`, and no answer files anywhere on disk.
- Yes, over the network. The same files are public on GitHub, and the agent has the internet (`task.toml:25`).

**(5) The three weakest points**
1. **Hidden answers reachable over the network.** `task.toml:25` (`network_mode = "public"`), plus the hidden datasets committed in a public repo, plus `tests/behavior.py:35` grading only those 2,000 fixed titles → Cheat 3.
2. **`no_python` checks names, not behaviour, and Python is on the grading machine.** `tests/grader_support.py:47-51` checks only `.py` names and symlinks.
   `tests/Dockerfile:1` is `python:3.12-slim-bookworm`, and `tests/grader_support.py:9` puts `/usr/local/bin` (where `python3` lives) on the worker's `PATH` → Cheat 2.
3. **`build` and `no_python` are free points.** `tests/reward.toml:4` gives them 2/6 of the reward, independent of `behavior` → Cheat 1.

## Strong points (what did NOT work)

- **The hidden answers are not on the agent's disk.** `task.toml:16` sets `environment_mode = "separate"`, and `environment/Dockerfile:3` copies only the Python library. Cheat 3 step A searched the agent container and found no answer files; `/tests` is absent (job `2026-11-19__14-28-22`, `agent/oracle.txt`).
- **The program cannot read `/tests` at grade time.** `rewardkit.Worker` runs the port as a fresh unprivileged UID and locks `/tests` to `0700 root` (rewardkit 0.2.4 `sandbox.py:79,122`). A "read `/tests/datasets/hidden_expected.txt` at run time" cheat is therefore blocked, so I did not spend a Harbor run on it.
- **Visible and hidden inputs share no titles.** I checked: 0 common lines. The visible files are not in the agent image either.
- **Partial ports get nothing from `behavior`,** because it is exact-match on the whole file.

---

## Cheat 1 — Delete + echo (build trick + delete trick)
What it does:   Deletes every file in `/workspace/repo`. Writes a `go.mod` and a `main.go` that copies stdin to stdout unchanged (`io.Copy`).
                No titlecase logic at all.
Score:          reward **0.3333**  (build 1, no_python 1, behavior 0)
Job folder:     `jobs/2026-11-19__14-26-09`
Result file:    `results/cheat1-reward.json` (per-check: `results/cheat1-reward-details.json`)
Why it worked:  `tests/reward.toml:4` gives `build` and `no_python` 2/6 of the reward on their own. `tests/build.py:23` checks only the exit code of `go build`.
                `tests/no_python.py:14-26` checks only that no `.py` names exist and that it builds. Neither check is tied to doing any real work.
How to fix:     Make `build` and `no_python` count only when `behavior` passes (gate them), or fold them into one pass/fail together with `behavior`.
                An empty Go program should score 0.

## Cheat 2 — Python inside (Go wrapper that runs the original Python)
What it does:   Saves `titlecase/__init__.py` as `tc_source.txt`, deletes every `.py` file, and embeds the source with `//go:embed`.
                At run time, `main.go` runs `python3 -I -S -c <driver> <source>`. The driver blocks the `regex` package (`sys.modules["regex"] = None`), loads the original library, and titlecases each line.
                No Go port is written; the Go code only launches Python.
Score:          reward **1.0**  (build 1, no_python 1, behavior 1)
Job folder:     `jobs/2026-11-19__14-27-23`
Result file:    `results/cheat2-reward.json` (per-check: `results/cheat2-reward-details.json`)
Why it worked:  1. `tests/grader_support.py:47-51`: `contains_python_file` checks only file **names** (`.endswith(".py")`) and symlinks. Python source in a `.txt` file passes.
                2. `tests/Dockerfile:1` (`FROM python:3.12-slim-bookworm`): the port runs in a machine that has `python3`, at `/usr/local/bin/python3`,
                   and `tests/grader_support.py:9` puts `/usr/local/bin` on the worker's `PATH`. `tests/behavior.py:20-24` runs the binary with no limit on starting other programs.
                3. The "no Python" rule in `instruction.md:18` is enforced only by name.
                Side finding: `tests/Dockerfile:8` installs `harbor-rewardkit`, which pulls in `regex` (`litellm` → `tiktoken` → `regex`; checked with `pip show regex` in that image).
                So a naive wrapper runs Python in regex mode and fails some titles. The cheat had to block `regex` to match `"regex_available": false` in `manifest.json:12`.
How to fix:     Removing Python from the verifier image is not possible: rewardkit's Worker itself starts as Python.
                Instead: (a) allow only `*.go`, `go.mod` and `go.sum` files in the submission, so a `.txt`/`.dat` holding Python source fails `no_python`;
                and (b) reject ports that can start processes: fail if `go list -deps ./...` includes `os/exec`, `syscall` or `plugin`.
                Tie (a) and (b) into `behavior`, so a wrapper scores 0, not 0.33.

## Cheat 3 — Read the exam from the public repo + lookup table
What it does:   Step A searches the local disk (`/tests`, `/solution`, home folders, and any `*expected*` / `*hidden*` / `answers*.txt` file) and finds nothing.
                Step B uses `curl` to download `tests/datasets/hidden_input.txt` and `hidden_expected.txt` from `raw.githubusercontent.com` (public repo, pinned commit).
                It embeds both files in a Go `map[input]answer` and prints a crude guess (capitalise each word) for any title not in the table. No titlecase logic.
Score:          reward **1.0**  (build 1, no_python 1, behavior 1)
Job folder:     `jobs/2026-11-19__14-28-22`
Result file:    `results/cheat3-reward.json` (per-check: `results/cheat3-reward-details.json`)
Proof it read the real exam: in the job's `agent/oracle.txt`, the downloaded files hash to `7a5dcf4b…be75f` and `31c56f65…aed22`,
                exactly the `hidden_input.txt` / `hidden_expected.txt` hashes in `tests/datasets/manifest.json:69-76`.
Why it worked:  1. `task.toml:25`: `network_mode = "public"` gives the agent internet access while it works.
                   The task needs no network: Go stdlib only, no module downloads (`instruction.md:15`).
                2. `tests/datasets/hidden_input.txt` and `hidden_expected.txt` are committed to a public GitHub repo, so "hidden" only means "not in the container".
                3. `tests/behavior.py:35` grades only those same 2,000 fixed titles. Every graded title is in the leaked table, so the fallback guess was never used.
How to fix:     Set `network_mode = "none"` for the agent in `task.toml:25`. That alone closes this route.
                Also: do not rely on hidden answers staying secret in a public repo.
                Use a much larger exam (the 100,000-title pool from Day 5) and/or grade on inputs that never appear in any file the agent can fetch.

---

## Summary

| Cheat | Idea | build | no_python | behavior | Reward | Job folder |
|---|---|---|---|---|---|---|
| 1 | Delete + echo | 1 | 1 | 0 | 0.3333 | `jobs/2026-11-19__14-26-09` |
| 2 | Python inside (Go wrapper runs original Python) | 1 | 1 | 1 | **1.0** | `jobs/2026-11-19__14-27-23` |
| 3 | Download hidden exam from public repo, lookup table | 1 | 1 | 1 | **1.0** | `jobs/2026-11-19__14-28-22` |

**Highest score any cheat got: 1.0 (Cheat 2 and Cheat 3; neither contains a titlecase port).**

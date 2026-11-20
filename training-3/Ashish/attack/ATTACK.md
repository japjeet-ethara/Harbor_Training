# Attack report — Omar Ghyas / titlecase-go

Target: Omar Ghyas
Commit attacked: `1aea2bf3fb67c8ec034a3c9467c011c4c65e1514`
Source: `OmarGhyas/titlecase-go` on branch `training-3`, copied into `attack/target/` without changes.

Verification done before writing this report:

- `git log -1 --format="%H %an %s" -- OmarGhyas/titlecase-go` returned `1aea2bf3fb67c8ec034a3c9467c011c4c65e1514 Omar Ghyas Add Omar Ghyas titlecase-go Harbor task with evaluation screenshots`.
- `git diff --no-index --stat -- OmarGhyas/titlecase-go Ashish/attack/target` returned no differences, so the copy matches the checkout byte for byte.
- `tests/data/visible.jsonl` and `tests/data/hidden.jsonl` each contain 2,000 lines.
- Omar's `cheat/` was read for understanding only. `environment/Dockerfile` has only two `COPY` instructions (lines 3-4) and neither copies `cheat/`, so it is not in the agent image.

## Step 4.1 — Read the task like an attacker

### 1. What files the agent can see inside the container

- `task.toml:2` — `artifacts = ["/workspace/repo"]`
- `task.toml:15` — `environment_mode = "separate"`
- `environment/Dockerfile:1-4`:
  - `FROM golang:1.23`
  - `WORKDIR /workspace/repo`
  - `COPY --exclude=.git python-titlecase /workspace/repo`
  - `COPY titlecase-go/tests/data/visible.jsonl /workspace/repo/visible.jsonl`

The agent works in `/workspace/repo`. That directory contains the entire Python `titlecase` source tree, including `titlecase/__init__.py`, plus `visible.jsonl` with 2,000 inputs and their expected answers. `tests/` and Omar's `cheat/` are not in the agent image. `task.toml:24` sets `network_mode = "public"`.

### 2. What `tests/test.sh` checks and how each check is scored

- `tests/test.sh:1-6` runs rewardkit against `/tests`, with `--workspace /workspace/repo` and `--output /logs/verifier/reward.json`:
  - `exec uvx --python '>=3.12,<3.14' --from 'harbor-rewardkit==0.2.*' \`
  - `rewardkit /tests \`
  - `--workspace /workspace/repo \`
  - `--output /logs/verifier/reward.json \`
  - `--max-concurrent-programmatic 1`
- `tests/reward.toml:1-4` — `aggregation = "weighted-mean"` and `weights = { build = 1.0, no_python = 1.0, behaviour = 4.0 }`, so the weights total 6.
- `tests/build.py:14-16` — `@criterion def build(workspace: Path) -> float: return 1.0 if go_build_succeeds(workspace) else 0.0`. `tests/support.py:15-27` runs `go build ./...` with a 120 second timeout.
- `tests/no_python.py:14-18` — returns 0.0 if any `.py` file exists, otherwise `1.0 if go_build_succeeds(workspace) else 0.0`. `tests/support.py:30-31` defines the check as `not any(path.suffix == ".py" for path in workspace.rglob("*") if path.is_file())`.
- `tests/behaviour.py:14-16` — `return behaviour_score(workspace)`. `tests/support.py:63-104` builds with `go build -o /var/grader/titlecase .` (line 70), runs the binary as `nobody` from `/var/grader` (lines 90-91), and scores exact line equality (lines 99-104) as `matches / len(cases)`.
- `tests/test_outputs.py:9-11` is only a placeholder `pass` test.

So `build` and `no_python` are 1.0 each without any correct answer, and `behaviour` is the only correctness check.

### 3. Which inputs the tests use and where they are stored

- `tests/support.py:9` — `HIDDEN_DATASET = Path("/tests/data/hidden.jsonl")`
- `tests/support.py:34-48` — reads that file as JSON lines and requires each record to have string `input` and `expected` fields (lines 41-44).
- `tests/support.py:82` — `payload = "\n".join(case["input"] for case in cases) + "\n"`, so all hidden inputs are fed to the program in one run.
- `tests/generate_data.py:15-16` — `CASE_COUNT = 2000` and `SEED = 1`; lines 22-23 set the visible and hidden paths under `tests/data/`.
- `tests/generate_data.py:371-377` — two independent random streams generate visible and hidden inputs; hidden inputs are generated with `blocked=set(visible_inputs)`.
- `tests/generate_data.py:380-381` — `if visible_set & hidden_set: raise RuntimeError("visible and hidden inputs overlap")`.
- `tests/generate_data.py:103-104,321` — line 103-104 require the reference module to have `REGEX_AVAILABLE`, and line 321 freezes each `expected` by calling `titlecase(text)`; `instruction.md:5` states "Match the `regex` behaviour."

The graded inputs are the 2,000 lines in `/tests/data/hidden.jsonl`. The agent can see the 2,000 visible lines and answers in `/workspace/repo/visible.jsonl` (`environment/Dockerfile:4`).

### 4. Whether `tests/` is visible to the agent while it works

No, according to the files:

- `task.toml:15` — `environment_mode = "separate"`, so the verifier environment is not the agent environment.
- `tests/Dockerfile:8-9` — `WORKDIR /tests` and `COPY . /tests/` put the tests in the verifier image only.
- `tests/Dockerfile:11-15` — the comment says "Root can read the hidden dataset. The program under test runs as nobody and cannot traverse this directory." It then applies `chmod 700` to directories and `chmod 600` to files, with only `test.sh` left executable.
- `environment/Dockerfile:1-4` — the agent image copies only `python-titlecase` and `visible.jsonl`; there is no `COPY` of `tests/`.
- `tests/support.py:12,90-91` — `PROGRAM_USER = "nobody"` and the graded binary runs with `user=PROGRAM_USER, cwd="/var/grader"`.

Therefore hidden answers should be unreachable by the agent and by the program it builds. A "read the exam" cheat should score 0 on `behaviour`.

### 5. The three weakest points of this exam

1. **A 0.3333 floor requiring no correct answers.** `tests/reward.toml:4` gives `build = 1.0` and `no_python = 1.0` out of total weight 6. `tests/no_python.py:14-18` only requires no `.py` files plus a successful build; `tests/build.py:14-16` only requires `go build ./...` to exit 0. A program that deletes the Python files and builds gets 2/6 = 0.3333 even if it prints nothing.
2. **The visible answer key is handed to the agent.** `environment/Dockerfile:4` copies `visible.jsonl` into `/workspace/repo`, and `tests/generate_data.py:318-325` writes each record as `{"input": ..., "expected": ...}`. `tests/support.py:99-104` grades exact output lines, so a lookup table can reproduce the visible answers. Honest caveat: `tests/generate_data.py:380-381` forbids overlap between visible and hidden inputs, so this cheat is expected to score 0 on `behaviour`; the measurement will confirm whether the hidden set really is different.
3. **Partial credit over a small, fixed, seeded exam.** `tests/reward.toml:4` gives `behaviour` weight 4.0 and `tests/support.py:104` returns a fraction of matched lines. `tests/generate_data.py:15-16,25-75` uses one seed and a limited pool of word families, so a half port that implements only the easy rules can earn a proportional share instead of zero.

What the exam defends well: hidden answers are permission-blocked (`tests/Dockerfile:13-15`), the graded binary runs as `nobody` (`tests/support.py:90-91`), visible and hidden inputs are disjoint (`tests/generate_data.py:380-381`), and the answer mode is stated (`instruction.md:5`).

## How we challenge every result (cheats 1, 2 and 3)

The same check is applied to every run before a number is written down:

1. The raw `verifier/reward.json` stays in the Harbor job folder. Only that file is copied into `attack/results/` as `<cheat>-reward.json`; the annotated copy adds the calculation below it but does not replace the job-folder proof.
2. Open `verifier/reward-details.json` and record each component's `score` and `weight`.
3. Recompute the weighted mean from `tests/reward.toml:4`: `(1×build + 1×no_python + 4×behaviour) / 6`, rounded to 4 decimals. If the arithmetic does not match `reward.json`, stop and investigate.
4. Independently verify the behaviour component where possible. For cheat 1, counting hidden records with `input == expected` gave `169/2000 = 0.0845`, exactly the reported behaviour score.
5. Independently verify `build` and `no_python`: copy the exact artifact workspace to scratch and run `go build ./...` in `golang:1.23` with `--network none`, and check for remaining `.py` files.
6. Trace any surprise to a `file:line` in the target, change only our cheat, re-run in a fresh scratch copy, and document both job folders. We never edit `target/`, its `tests/`, `task.toml`, or `environment/`.

The full cheat 1 arithmetic and challenge log are also stored in `attack/results/cheat1-reward.json`.

## Cheat 1 — Lookup table

**What it does:** A Go program reads `/workspace/repo/visible.jsonl`, maps each visible `input` to its `expected` answer, and prints the mapped answer for any matching stdin line. For unseen input it echoes the line unchanged — a fixed guess, not a titlecase port. It deletes all `.py` files and the leftover `titlecase/` directory so the workspace builds as a clean Go module.

**Score:** reward 0.3897 (build 1, no_python 1, behaviour 0.0845)

**Job folder:** `2026-11-19__16-21-03` (trial `titlecase-go__hHE435k`). Reward file copied from `verifier/reward.json` to `attack/results/cheat1-reward.json`.

**Why it worked:** `environment/Dockerfile:4` copies `visible.jsonl`, with its `input` and `expected` fields (`tests/generate_data.py:318-325`), into the agent workspace, so the lookup table is built from answers handed to the agent. `tests/reward.toml:4` gives `build` and `no_python` 1.0 each out of weight 6, and `tests/no_python.py:14-18` requires only no `.py` files plus a successful build. The 0.0845 behaviour component is 169/2000 hidden cases where `input == expected`: `tests/support.py:99-104` scores exact line matches, and `tests/generate_data.py:380-381` blocks visible/hidden overlap, so the memorised answers contribute nothing and only the unchanged-input guess matches.

A first attempt scored 0.0563 (job `2026-11-19__15-29-28`, breakdown build 0, no_python 0, behaviour 0.0845) because the script left the empty `titlecase/` directory behind. With `module titlecase` in `go.mod`, `go build ./...` then fails with `go: build output "titlecase" already exists and is a directory`; `tests/support.py:19` scores `build` 0 and `tests/no_python.py:18` then scores `no_python` 0. Adding `rm -rf /workspace/repo/titlecase` fixed the cheat, not the exam.

**How to fix:** Do not put the visible answers where the agent can read them (`environment/Dockerfile:4`), and make `no_python` conditional on real behavioural correctness rather than paying 2/6 for deleting files (`tests/no_python.py:14-18`, `tests/reward.toml:4`). Expand the hidden inputs so that echoing the input unchanged cannot match (`tests/generate_data.py:25-75`).

## Cheat 2 — Half port

**What it does:** A Go program that implements only the easy rules from `titlecase/__init__.py`: split on whitespace while preserving the original separators, uppercase the first letter of each word, lowercase small words except at the first and last position, and capitalise those first/last small words. It deliberately does not implement acronyms, mixed case, apostrophes, all-caps lines, Mac/Mc, honorifics, hyphens, slashes, or subphrase recasing. It deletes `.py` files and `titlecase/` so the workspace builds.

**Score:** reward 0.7213 (build 1, no_python 1, behaviour 0.582)

**Job folder:** `2026-11-19__16-43-35` (trial `titlecase-go__Ko3hGEW`). Raw reward copied from `verifier/reward.json` to `attack/results/cheat2-reward.json`; the annotated copy holds the calculation and challenge log.

**Why it worked:** `tests/reward.toml:4` again pays 2/6 for `build` and `no_python` (`tests/build.py:14-16`, `tests/no_python.py:14-18`). The 0.582 behaviour component is 1164/2000 exact hidden matches: I rebuilt the same Go source in `golang:1.23` with `--network none`, fed all hidden inputs through the binary exactly as `tests/support.py:82-104` does, and counted 1164 matching lines. That matches `reward-details.json` exactly. The 836 misses are concentrated in the deliberately skipped rules, which is the portion the full port in `solution/solve.sh` recovers.

**Challenge performed:** `(4×0.582 + 1 + 1)/6 = 4.328/6 = 0.721333… → 0.7213` ✓. The exact artifact workspace was copied to scratch: `go build ./...` exited 0 and there were 0 `.py` files, so `build=1` and `no_python=1` are genuine. No component disagreed, so no re-run was needed.

**How to fix:** Remove the unconditional 2/6 floor by tying `build` and `no_python` to behavioural correctness (`tests/reward.toml:4`, `tests/no_python.py:14-18`). Make `behaviour` an all-or-nothing threshold or add enough hard-category cases (`tests/generate_data.py:64-75`) that a half port cannot collect 0.582 of the score.

## Cheat 3 — Silent binary

**What it does:** A Go program that consumes every stdin line and emits nothing. It deletes `.py` files and `titlecase/` so the workspace builds, but performs no titlecasing at all. This isolates the scoring floor with zero correct answers.

**Score:** reward 0.3333 (build 1, no_python 1, behaviour 0)

**Job folder:** `2026-11-19__16-48-15` (trial `titlecase-go__TAYJotC`). Raw reward copied from `verifier/reward.json` to `attack/results/cheat3-reward.json`; the annotated copy holds the calculation and challenge log.

**Why it worked:** `tests/reward.toml:4` pays 1.0 each for `build` and `no_python` out of total weight 6, and `tests/no_python.py:14-18` only requires no `.py` files plus a successful build. With `behaviour = 0`, the reward is exactly `2/6 = 0.3333`. `tests/support.py:96-104` compares output lines to expected answers; an empty stdout gives zero matches out of 2,000.

**Challenge performed:** `(4×0 + 1 + 1)/6 = 2/6 = 0.3333` ✓. The exact artifact workspace was copied to scratch: `go build ./...` exited 0, there were 0 `.py` files, and rebuilding then feeding all 2,000 hidden inputs produced `OUTPUT_BYTES=0`. Every component matches, so no re-run was needed.

**How to fix:** Remove the unconditional 2/6 floor (`tests/reward.toml:4`) by making `build` and `no_python` prerequisites for behaviour rather than independently paid points (`tests/build.py:14-16`, `tests/no_python.py:14-18`). A correct score should require nonzero behavioural correctness.

## Summary of measured cheats

| Cheat | Job folder | build | no_python | behaviour | Reward |
| --- | --- | ---: | ---: | ---: | ---: |
| 1 — lookup table | `2026-11-19__16-21-03` | 1 | 1 | 0.0845 | 0.3897 |
| 2 — half port | `2026-11-19__16-43-35` | 1 | 1 | 0.582 | 0.7213 |
| 3 — silent binary | `2026-11-19__16-48-15` | 1 | 1 | 0 | 0.3333 |

All three numbers come from real Harbor runs with `-a oracle` on scratch copies outside `attack/target/`. Only the raw `verifier/reward.json` from each job was copied into `attack/results/`; the annotated copies add the calculation and challenge log while the untouched source stays in each job folder. No target file, `task/` file, or `environment/` file was changed.

**Highest score any cheat got: 0.7213 — cheat 2 (half port), job `2026-11-19__16-43-35`.**

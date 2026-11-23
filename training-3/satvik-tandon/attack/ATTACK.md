# Day 4 review of Priya Kumari’s titlecase task

I ran three deliberately incomplete Go programs against Priya’s original verifier. The strongest was simple capitalization at **0.6543**, even though it got fewer than half of the titles right. All three built successfully and passed the Python-file check. Even echoing the input unchanged earned **0.3867**.

## What Harbor grades

- **Agent workspace.** The agent image starts with Go 1.23 and copies the bundled Python reference into `/workspace/repo`. This includes the implementation, upstream tests, and rule examples. The Dockerfile removes the upstream Git metadata. See `environment/Dockerfile:1`, `environment/Dockerfile:4`, and `environment/Dockerfile:5`.
- **Verifier workspace.** Harbor collects `/workspace/repo` and uses a separate verifier environment. The verifier image copies the grading files to `/tests`. The agent image has no corresponding copy of that directory. See `task.toml:2`, `task.toml:15`, `environment/Dockerfile:4`, and `tests/Dockerfile:13`.
- **Inputs and scoring.** The fixture generator writes visible and hidden files under `tests/data/`. The verifier uses `hidden_inputs.txt` and `hidden_expected.txt`. It grades 2,000 titles. A line-count mismatch earns zero for behaviour. Otherwise each exact line match counts equally. See `tests/gen.py:17`, `tests/gen.py:245–250`, `tests/behaviour.py:7–8`, and `tests/behaviour.py:11–19`.
- **Reward.** The verifier entry point calls RewardKit and writes `reward.json`. Build and no_python each have weight 1, and behaviour has weight 4. The combined reward is `(build + no_python + 4 × behaviour) / 6`. See `tests/test.sh:6–9`, `tests/reward.toml:2–4`, `tests/build.py:15`, and `tests/no_python.py:24–29`.

## Three measured submissions

| Submission | Build | No Python | Behaviour | Harbor reward | Harbor job folder |
|---|---:|---:|---:|---:|---|
| 1. Echo | 1 | 1 | 0.0800 | 0.3867 | `jobs/satvik-day4-20261118-162511-cheat1` |
| 2. Capitalize word starts | 1 | 1 | 0.4815 | 0.6543 | `jobs/satvik-day4-20261118-162511-cheat2` |
| 3. Add interior small words | 1 | 1 | 0.4695 | 0.6463 | `jobs/satvik-day4-20261118-162511-cheat3` |

### 1. Echo

The program copies stdin to stdout. It earns both packaging checks and matches 8% of the hidden lines because those inputs are already in the expected form. It leaves `hello world` unchanged where the reference returns `Hello World`. See `tests/data/hidden_inputs.txt:269` and `tests/data/hidden_expected.txt:269`.

**Weakness and fix.** Packaging alone contributes one third of the total, even with zero correct lines. Make build and no_python prerequisites for earning a behaviour score. The final score for a qualifying program can then equal its behaviour score. See `tests/reward.toml:4`.

### 2. Capitalize the first letter of every word

The program splits each title on whitespace, uppercases the first character of each word, and joins the words with single spaces. It produces `This Vs. That` for `this vs. that`. The reference keeps the interior `vs.` lowercase. See `tests/data/hidden_inputs.txt:472` and `tests/data/hidden_expected.txt:472`.

**Weakness and fix.** Ordinary titles can pass this rule, while errors on interior small words and spacing cost only the affected lines. Grade paired examples that move the same small word between the start, middle, and end. Include repeated-space examples and report those results separately. See `tests/gen.py:201–204` and `tests/behaviour.py:16–19`.

### 3. Add interior small words

The program lowercases recognized small words inside a title and capitalizes ordinary word starts. It still emits `Mcclelland` for `mcclelland`, where the reference returns `McClelland`. See `tests/data/hidden_inputs.txt:39` and `tests/data/hidden_expected.txt:39`.

**Weakness and fix.** The generator samples from a fixed list of rule examples and appends titles without deduplicating them. The hidden file contains 1,716 distinct titles across 2,000 rows. Repeated cases receive full weight each time. Generate distinct variations for prefixes, apostrophes, and subphrase boundaries, then check accuracy for each family alongside the aggregate. See `tests/gen.py:85`, `tests/gen.py:207–208`, `tests/gen.py:222–226`, and `tests/behaviour.py:16–19`.

## Verification notes

I verified the target files against commit `02684e6e2e8a31edc7fed5acd21fd507c496b637`. Each scratch copy differed from that target only in `solution/solve.sh`. I copied the three final rewards from the corresponding Harbor verifier directories. The component scores above come from their sibling `reward-details.json` files.

The first pass left an empty `titlecase/` directory after removing the Python source. Go reported that its default executable path was already a directory. All three first-pass jobs earned 0.0 (`jobs/satvik-day4-20261118-162204-cheat1`, `jobs/satvik-day4-20261118-162204-cheat2`, and `jobs/satvik-day4-20261118-162204-cheat3`). Removing the empty directory in each installer allowed Harbor to evaluate the intended Go behaviour.

Highest measured reward across the final submissions: **0.6543** (submission 2).

## Day 6 re-attack of Priya's hardened task

I tested Priya's task as present at branch commit `041dff11a03ba7312ed647fc4d3d876848b9f92c`;
the latest commit changing her task was `ce43152ea0d5405c7a1c63fc10c050ab002431d0`.
Each valid run used the committed task files unchanged and replaced only
`solution/solve.sh` in an ignored scratch copy. The first local attempt had
Windows-converted CRLF line endings in `tests/test.sh` and produced no reward;
I excluded it and rebuilt the scratch copies from Git's raw blobs.

| Submission | Behaviour | Reward | Harbor job | Saved reward |
| --- | ---: | ---: | --- | --- |
| Cheat 1: echo | 0.0137 | **0.3425** | `jobs/priya-day6-cheat1-exact` | `results/recheat1-reward.json` |
| Cheat 2: capitalize word starts | 0.1090 | **0.4060** | `jobs/priya-day6-cheat2-exact` | `results/recheat2-reward.json` |
| Cheat 3: add small-word rules | 0.1341 | **0.4227** | `jobs/priya-day6-cheat3-exact` | `results/recheat3-reward.json` |

The new 100,000-title exam reduced the three original programs' behaviour
shares, but all three rewards remain above 0.2. `tests/reward.toml:4` still
weights `build` and `no_python` at 1 each and behaviour at 4. The first two
checks pass for these Go programs, so they receive one-third of the reward
before any title is right. Make those checks prerequisites and award the final
reward from exact behaviour only; this removes the structural baseline without
discarding partial accuracy.

**Highest Day 6 re-attack reward: 0.4227 (cheat 3).**

### Hardened oracle check

I also ran Priya's committed `solution/solve.sh` unchanged on the same task.
Harbor awarded **0.9943** (`behaviour` raw **0.99143**) in
`jobs/priya-day6-oracle-exact`; the reward is saved as
`results/priya-oracle-reward.json`. This is 857 wrong titles out of 100,000,
matching the *before-fix* count in her measurement files. Her `HARDEN.md`
reports 0 wrong after fixing leading underscores, but the committed
`task/solution/solve.sh:263` still skips every punctuation character in
`capFirst()` without the reported underscore exception. The submitted oracle
script needs the fix and a new Harbor oracle run; changing the exam to hide
those errors would not repair the port.

## Follow-up: current branch recheck

I fetched `origin/training-3` and reran the three original cheats and Priya's
committed oracle against her task at commit
`08c76937d2903ee9cdc504b1a27dbded0f0bba3e`. Since the preceding Day 6
run, her only changed file was `HARDEN.md`; the task files were unchanged.
The fresh Harbor runs had no exceptions:

| Run | Reward | Fresh Harbor job | Saved reward |
| --- | ---: | --- | --- |
| My cheat 1: echo | **0.3425** | `jobs/priya-rerun-cheat1-exact` | `results/confirm-cheat1-reward.json` |
| My cheat 2: capitalize word starts | **0.4060** | `jobs/priya-rerun-cheat2-exact` | `results/confirm-cheat2-reward.json` |
| My cheat 3: add small-word rules | **0.4227** | `jobs/priya-rerun-cheat3-exact` | `results/confirm-cheat3-reward.json` |
| Priya's committed oracle | **0.9943** | `jobs/priya-rerun-oracle-exact` | `results/confirm-oracle-reward.json` |

All three of my cheats remain above the required **below 0.2** target.
Priya's `HARDEN.md:13-15` describes a different set of cheats and reports
scores 0.1355, 0.1684 and 0.2205. Even its third reported score is above
0.2, despite the `DEFENDED` label. These reported scores do not describe
the three programs in my `attack/cheat1-3/` folders.

The report also says the verifier weights are 1:1:23 and that `no_python.py`
has a canonical smoke test (`HARDEN.md:7,27-29`). The current submitted files
still have 1:1:4 weights (`task/tests/reward.toml:4`), and `no_python.py:23-29`
only checks for Python files and a successful Go build. The reported oracle
fix is likewise absent from `task/solution/solve.sh:263`. The fresh oracle
reward remains 0.9943, below the required 1.0.

## Latest re-attack: Priya's Day 6 proof commit

Priya then pushed `ed95cf832935b14ea964187aea04bb0fe45be745`, which changes
the submitted task itself: `reward.toml` now weights behaviour at 23,
`no_python.py` runs a four-case correctness smoke test, and the oracle has
the leading-underscore fix. I rebuilt each scratch task from that commit's
Git blobs and changed only `solution/solve.sh` for my three cheats. These
fresh Harbor runs supersede the scores above for the **current** task:

| Run | Reward | Harbor job | Saved reward |
| --- | ---: | --- | --- |
| My cheat 1: echo | **0.0526** | `jobs/priya-current-cheat1` | `results/current-cheat1-reward.json` |
| My cheat 2: capitalize word starts | **0.1403** | `jobs/priya-current-cheat2` | `results/current-cheat2-reward.json` |
| My cheat 3: add small-word rules | **0.1634** | `jobs/priya-current-cheat3` | `results/current-cheat3-reward.json` |
| Priya's committed oracle | **1.0000** | `jobs/priya-current-oracle` | `results/current-oracle-reward.json` |

**Current outcome:** Priya's oracle reaches 1.0 and all three of my original
cheats are below 0.2. The earlier follow-up records the preceding commit
and must not be read as the current task's outcome. Her `HARDEN.md` and
`DEFENCE.md` still report 0.2205 for a different cheat 3; that reported
score remains above the stated below-0.2 target for that particular cheat.

## One new Day 6 cheat: compact rule heuristic

On the same current commit, I submitted `attack/cheat4/solve.sh` in a scratch
copy where **only `solution/solve.sh` was replaced**. This cheat writes a
small Go program. It handles small words, existing internal capitals, `Mc`
names, domain-like words and hyphenated compounds (`attack/cheat4/solve.sh:22-70`).
It does not fetch the public answer file or implement the full reference port.

| Run | Build | No Python | Exact behaviour | Final reward | Harbor job | Saved reward |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| New cheat 4 | 1.0 | 1.0 | 0.19942 (19,942/100,000) | **0.2635** | `jobs/priya-current-cheat4-rule-heuristic` | `results/current-cheat4-reward.json` |

The general rules happen to satisfy all four canonical smoke cases in
`task/tests/no_python.py:8-44`, so this incomplete program earns the
`no_python` point. The verifier's weights in `task/tests/reward.toml:4`
then give `(1 + 1 + 23 * 0.19942) / 25 = 0.2635` after rounding. The
score exceeds the Day 6 below-0.2 target, even though the program gets
about 80% of the exam wrong.

**Fix:** Keep the no-Python check about language compliance and use the
100,000-case exact-match fraction as the reward once build and compliance
pass. Under that rule this same cheat would score 0.19942. Alternatively,
the exam could cover more of the general rules this heuristic misses; any
change should preserve the required 100,000 cases and oracle score 1.0.

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

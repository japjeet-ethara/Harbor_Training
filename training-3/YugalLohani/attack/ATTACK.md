# Attack report — Charitra's `titlecase-go`

**Attacker:** Yugal Lohani
**Target:** Charitra, `charitra/titlecase-go`
**Repository:** `https://github.com/japjeet-ethara/Harbor_Training`, branch `training-3`
**Target commit attacked:** `8caffa1fb84685a05d40a66ecf82ce4ff883dae6`
(the task tree is identical to the earlier `c8ea6d9`; that commit only added `Attack.md.md`)
**Harbor:** 0.26.0, Docker 28.3.0, local Docker machine, 2026-11-20.

All three cheats replace only `solution/solve.sh`. `tests/`, `task.toml` and
`environment/` were never changed. Each ran on a private copy of the task.

## Baselines (sanity check on an untouched copy)

| Run | reward | Job folder |
|---|---|---|
| their oracle | 1.000 | `jobs/2026-11-18__23-44-35` |
| nop | 0.000 | `jobs/2026-11-18__23-47-25` |

## Scoring recap

`reward = (1*build + 1*no_python + 4*behaviour) / 6` (`tests/reward.toml:4`). So any
program that compiles and leaves no `.py` file scores at least `2/6 = 0.333` before a
single correct answer. `behaviour` is graded on 2,000 hidden inputs that are disjoint
from the visible ones (`tests/grader.py:149`, `Public and hidden inputs overlap`).

**Independent check (not via Harbor):** reading the target's own fixtures, the hidden and
visible input sets share 0 records, and exactly 53 of the 2,000 hidden inputs satisfy
`titlecase(x) == x`. That 53 is precisely cheat 1's behaviour match count, which confirms
its lookup table contributed nothing and only the echo fallback scored.

## A fourth vector I analysed and did not pursue: read the hidden answers at run time

A natural cheat is to read `/tests/data/hidden_*` at run time. It cannot work here, so I
did not spend a cheat slot on it. The grader runs each candidate through RewardKit's
`Worker` with `private_paths=(TESTS, LOGS, PRIVATE, workspace)` (`tests/grader.py:166-170`).
`Worker` chmods those paths to `0o700` owned by root and then runs the candidate as a
freshly allocated non-root UID (`rewardkit/sandbox.py:122`, and `user=uid, group=uid` at
`sandbox.py:187`). So `/tests` is unreadable to the candidate, and the hidden answers live
nowhere else in its view. This defence is sound.

---

## Cheat 1 — Lookup table

**What it does:** a Go program that, at run time, reads the visible answer sheet shipped
in the workspace (`visible/inputs.txt`, `visible/expected.txt`), prints the stored answer
when the input matches, and echoes the input unchanged on a miss. It deletes the upstream
`.py` files so the no_python point is earned. No titlecase logic.

**Score:** reward **0.351** (build 1, no_python 1, behaviour 0.0265 = 53/2000).
**Job folder:** `jobs/2026-11-20__05-31-27` (reward in `results/cheat1-reward.json`).

**Why it worked (and mostly did not):** the 0.333 comes only from build + no_python. The
behaviour score is almost zero because the hidden inputs are disjoint from the visible
ones, enforced at `tests/grader.py:146-149` (`set(inputs) & set(hidden_inputs)` must be
empty). The 53 matches are inputs where `titlecase(x) == x`, so the echo fallback happens
to be right. This confirms the disjoint-hidden design is sound; the lookup gains nothing.

**How to fix:** nothing to fix for the lookup itself. The only leakage is that the build
+ no_python floor (0.333) is above the 0.2 bar. See the shared fix at the end.

---

## Cheat 2 — Half port

**What it does:** a genuine but deliberately incomplete Go port that implements the easy
rules a careless agent would: lower an all-caps line first, capitalize the first letter of
each space-separated word (skipping leading punctuation) and lower the rest, and lower the
NYT small words except at the first and last position. It implements none of the hard
rules (Mc/Mac, apostrophes, hyphen/slash parts, all-consonant acronyms, preserved inner
caps, inline periods, sub-phrases after punctuation, Unicode full case mapping, non-space
whitespace). Deletes the `.py` files.

**Score:** reward **0.3717** (build 1, no_python 1, behaviour 0.0575 = 115/2000).
**Job folder:** `jobs/2026-11-20__06-57-01` (reward in `results/cheat2-reward.json`).

**Why it worked (and mostly did not):** again essentially only the 0.333 floor. Even a
plausible half port that handles small words, all-caps lines and leading punctuation
matches just 115 of 2,000, because the hidden set is adversarial: its inputs are full of
punctuation, mixed case, hyphens/slashes and Unicode. This is a strong result for the
exam: a naive port earns almost no behaviour credit, exactly the brief's Lesson 1 (weird
inputs beat a half-right port).

**How to fix:** nothing specific; the behaviour check already punishes a half port well.
The residual 0.3717 is the build + no_python floor plus a little behaviour credit.

---

## Cheat 3 — Python inside (the real hole)

**What it does:** no Go port at all. `solve.sh` copies the original
`titlecase/__init__.py` to a non-`.py` data file (`tc_src.txt`), then writes a tiny Go
`main` that, at run time, writes that source to `/tmp` and runs `python3` on it to
titlecase stdin. It forces the stdlib `re` fallback (`sys.modules['regex'] = None`) so the
output matches the task's stated mode. After building, it deletes every `.py` file under
the repository, so none remains there.

**Score:** reward **1.000** (build 1, no_python 1, behaviour 1.000 = 2000/2000).
**Job folder:** `jobs/2026-11-20__06-58-09` (reward in `results/cheat3-reward.json`,
`matched_records: 2000` in `results/cheat3-grade-details.json`).

**Robustness:** the source file is located dynamically, several interpreter names and
absolute paths are tried, and if no interpreter exists the program degrades to a naive
in-Go port instead of crashing (so even against a hardened task it keeps the build +
no_python floor rather than scoring a `command_failed` zero on behaviour).

**Why it worked:** two facts combine.
1. The separate verifier image is `python:3.12-slim-bookworm` (`tests/Dockerfile:3`) and
   the candidate is run with `PATH` including `/usr/local/bin` and `/usr/bin`
   (`tests/grader.py:33`), so `python3` is on the candidate's `PATH` inside the grader's
   run sandbox, with network off (Python needs none here).
2. The `no_python` check is purely a filename scan for `*.py` under the repo
   (`tests/grader.py:156-161`, `241`); it does not detect that a `.go` program shells out
   to an interpreter. The "no external interpreter" requirement exists only as prose in
   `instruction.md:19`, with no check behind it. So the original implementation runs
   verbatim and `behaviour` is a perfect 1.0.

This is the strongest cheat: a full 1.0 with zero Go titlecase logic.

**How to fix (for Charitra, Day 5):**
- Remove Python from the candidate run environment: build and run candidates on a Go-only
  image (as my own task does: `golang:1.23-alpine` with no interpreter), or strip
  `python3`/`python` from the `Worker`'s `PATH` / the run image, so `exec.LookPath` fails.
- Optionally, scan the submitted Go sources for `os/exec` use of an interpreter, or run
  the candidate with no access to `/usr/local/bin` and `/usr/bin`.
- The filename-only `no_python` check should not be relied on to stop interpreter use;
  pair it with an interpreter-free run sandbox.

---

## Highest score

**The highest score any cheat reached is 1.000 (cheat 3, Python inside),
job `jobs/2026-11-20__06-58-09`.** Cheats 1 and 2 reached only the 0.333 build + no_python
floor (0.351 and 0.3717). The one real vulnerability is that the grader's run sandbox
contains a Python interpreter, which lets a Go wrapper run the original code and score 1.0.
The disjoint hidden set (cheat 1), the adversarial hidden inputs (cheat 2) and the
non-root fresh-UID `Worker` isolation (the read-the-exam vector) all held.

---

## Day 6 re-attack — Charitra's hardened task

**Target now:** `training-3/Charitra/task` at commit
`be2c020e946186669c9810d1517f46b3895691f8` (Charitra's Day 5 hardened version).
Re-ran the same three cheats. Harbor 0.26.0, 2026-11-20.

| Cheat | Day 4 (original task) | Day 6 (hardened task) | Job folder |
|---|---|---|---|
| cheat1 lookup | 0.351 | **errored, no reward** | `attack/jobs/2026-11-20__13-53-15` |
| cheat2 half-port | 0.3717 | **errored, no reward** | `attack/jobs/2026-11-20__13-54-19` |
| cheat3 python-inside | 1.000 | **errored, no reward** | `attack/jobs/2026-11-20__13-55-07` |

**What happened:** none of the three cheats could be scored, because the
hardened task no longer runs. Its verifier fails at config load, before any
candidate is built, with:

```
ValueError: /tests/reward.toml: unknown [[reward]].weights inputs: 'build'.
            Available inputs: 'behaviour', 'no_python'.
```

Charitra's hardening changed `tests/reward.toml` to
`weights = { build = 0.1, no_python = 0.1, behaviour = 5.8 }` but removed the
`tests/build/` check directory (only `tests/behaviour/check.py` and
`tests/no_python/check.py` remain). Reward Kit validates the reward weights
against the available check names and raises, so the grader writes no
`reward.json`; Harbor reports each trial as a `RewardFileNotFoundError` rather
than a score.

**Effect:** the hardening is a regression. The python-inside hole I found on
Day 4 (which scored 1.0) is moot only because the whole task is now ungradeable
— the oracle cannot score 1.0 either. This should be reported to Charitra: the
fix is to restore a `tests/build/` check (or drop `build` from the reward
weights) so the task runs again, and then re-close the python-inside hole
(remove the interpreter from the verifier run environment and isolate the
candidate, as noted in Finding / cheat 3 above).

**Highest re-attack score: none (all trials errored).**

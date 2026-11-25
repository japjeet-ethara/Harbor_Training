# Attack review: titlecase-go

- **Task author:** Priyanshu Singh
- **Pinned commit:** `ef58d2a95f5a6b3ee782d878b7bdb6c19088cbac`
- **Task folder:** `PriyanshuSingh/titlecase-go`

All file paths and line numbers below are relative to `PriyanshuSingh/titlecase-go` at this commit.

The three cheat scripts are in this `attack/` folder. Harbor ran each one as the task's solution in a disposable copy of the task. The scores come from each job's `verifier/reward.json`; copies are in `results/`.

## How the grader gives points

`tests/test.sh:12-13` runs three checks with Reward Kit:

| Check | Weight | What it checks | Where |
|---|---|---|---|
| build | 1 | `go build ./...` passes | `tests/checks/build/build.py:4` |
| no_python | 1 | No `.py` files are left, and the build passes | `tests/checks/no_python/no_python.py:14-19` |
| behaviour | 4 | Share of the 2,000 hidden titles whose output line is exactly right | `tests/checks/behaviour/behaviour.py:50-52` |

The weights are in `tests/checks/reward.toml:3-4`. The final reward is a weighted mean:

```
reward = (1 × build + 1 × no_python + 4 × behaviour) ÷ 6
```

Only behaviour looks at what the program prints. build and no_python together are worth 2 of 6 points (0.3333). Any program that compiles gets them, as long as the Python files are deleted.

## Cheat 1: echo the input

- **Script:** `cheat1/solve.sh`
- **Job folder:** `jobs/2026-11-18__21-49-24`

**What it did.** It wrote a small Go program that copies stdin to stdout unchanged with `io.Copy`. It deleted every `.py` file and checked that `go build ./...` passes. It ports none of the titlecase rules.

| build | no_python | behaviour | reward |
|---|---|---|---|
| 1.0 | 1.0 | 0.0735 | **0.3823** |

**Why echo earned 0.3823.**

- **build = 1.0.** The program is valid Go, and `tests/checks/build/build.py:4` only asks that it compiles.
- **no_python = 1.0.** The script deleted the `.py` files. `tests/checks/no_python/no_python.py:14-19` checks only for `.py` files and the build.
- **behaviour = 0.0735 = 147 ÷ 2,000.** Titlecase leaves 147 of the hidden titles unchanged. They include:
  - mixed-case words such as `macOS` and `mIxEd`;
  - titles that are already correct;
  - the one empty line (`tests/gen.py:177-179`).

  Copying the input gets these 147 right for free. `tests/checks/behaviour/behaviour.py:51-52` counts every matching line. It does not check whether the program did any work.
- **reward = (1 + 1 + 4 × 0.0735) ÷ 6 = 2.294 ÷ 6 = 0.3823.**

When build and no_python both pass, a program that matches zero titles earns 0.3333 (README.md:23). Echo matched 147 of the 2,000 hidden titles, bringing its measured reward to 0.3823. That exceeds the README’s 0.2 cheat target (README.md:11).

**Why "at least one correct answer" would not stop it.** The README suggests giving the build and no_python points only when behaviour is above zero (`README.md:19`). Echo already has 147 correct answers, so its behaviour is above zero. It would pass that rule and keep the full 0.3823. Asking for one correct answer is too easy, because copying the input gives correct answers without porting anything.

**Proposed fix.**

1. Make build and no_python pass/fail conditions instead of points. If both pass, reward = behaviour. If either fails, reward = 0. Echo would then score 0.0735 instead of 0.3823.
2. Give no behaviour points for titles that titlecase does not change. For example, score only the 1,853 hidden titles whose answer differs from the input, and test the empty line in a separate check. Echo would then score 0 for behaviour.

## Cheat 2: capitalise the first letter of every word

- **Script:** `cheat2/solve.sh`
- **Job folder:** `jobs/2026-11-18__22-19-42`

What it did. The Go program capitalises the first letter of each whitespace-delimited word if that letter is a through z. It copies everything else unchanged. For example, it turns the rise of AI into The Rise Of AI. The expected output is The Rise of AI.

| build | no_python | behaviour | reward |
|---|---|---|---|
| 1.0 | 1.0 | 0.204 | **0.4693** |

**Comparison with Cheat 1.**

- Cheat 2 matched 408 of 2,000 hidden titles (20.4%). Cheat 1 matched 147 of 2,000 (7.35%). That is 261 more titles, about 2.8 times as many.
- The reward rose from 0.3823 to 0.4693: (1 + 1 + 4 × 0.204) ÷ 6 = 2.816 ÷ 6 = 0.4693.
- **Why one rule gets so many titles right.** Titlecase capitalises the first letter of most words. Some titles have no small word (such as "of") in the middle and none of the special words: Mc names, apostrophe names, acronyms, mixed case. For those titles, the one-line rule gives exactly the same answer. For example, `river story` becomes `River Story` either way.
- **Offline check.** I applied the same rule to `tests/data/hidden_inputs.txt` and compared the result with `tests/data/hidden_expected.txt`. It reproduced the 408 exactly:
  - 134 are titles that echo also got right;
  - 274 are new;
  - 13 of echo's titles were lost, because the rule capitalised words that titlecase leaves alone, such as `macOS`.

  So 147 − 13 + 274 = 408.

**The grader lines that explain it.** `tests/checks/behaviour/behaviour.py:51-52` gives full credit for every matching title, however the program produced it. Nothing compares the score with what a simple rule would get. Add the fixed 2 of 6 points from `tests/checks/reward.toml:4`, and one simple rule scores more than twice the 0.2 cheat target.

**Proposed fix.**

1. Score only titles that need at least one real titlecase rule. When making the data, drop (or test separately) the titles that echo or this first-letter rule already get right. By the same offline check, 1,579 of the 2,000 hidden titles remain. Both cheats would then score 0 for behaviour.
2. Change the hidden set (`tests/gen.py:111-146`) so fewer titles can be solved by capitalising every word, for example by adding more titles with small words in the middle.
3. Add echo and this first-letter rule to the cheat results in the README (`README.md:7-11`), so every new version of the task is checked against them.

Fix 1 from Cheat 1 is not enough on its own here. With it, Cheat 2 would still score 0.204, which is above the 0.2 target.

## Cheat 3: echo plus one extra line

- **Script:** `cheat3/solve.sh`
- **Job folder:** `jobs/2026-11-18__22-34-31`

**What it did.** It is the same as Cheat 1, but after copying all of stdin the program prints one extra line: `EXTRA_OUTPUT_MARKER`. If the input does not end with a newline, the program adds one first, so the marker is always on its own line. The hidden input file ends with a newline, so the marker became line 2,001 of the output.

| build | no_python | behaviour | reward |
|---|---|---|---|
| 1.0 | 1.0 | 0.0735 | **0.3823** |

**What the equal scores show.** Cheat 3 printed one line more than there were inputs, and lost nothing: every score is equal to Cheat 1's. So the extra line was never counted against it.

The instruction describes the output as one result line for each input line, in order (`instruction.md:15-18`). It does not mention extra lines, and the grader does not check for them. In `tests/checks/behaviour/behaviour.py:50-52`:

- the output is split into lines;
- Python's `zip` pairs those lines with the 2,000 expected lines and stops at the shorter list, so line 2,001 is never looked at;
- the score is divided by the number of expected lines (`len(expected)`), not by the number of output lines.

From reading the same code (not measured): an extra line at the start would shift every line by one and lose almost all matches. Only extra lines at the end go unnoticed.

**Proposed fix.** Count the output lines before comparing. If the program prints more or fewer lines than there are inputs, either give behaviour 0, or count every extra line as a wrong answer by dividing by the larger of the two line counts.

## Summary

| Cheat | Job folder | build | no_python | behaviour | reward |
|---|---|---|---|---|---|
| 1: echo | `jobs/2026-11-18__21-49-24` | 1.0 | 1.0 | 0.0735 | 0.3823 |
| 2: first letter | `jobs/2026-11-18__22-19-42` | 1.0 | 1.0 | 0.204 | 0.4693 |
| 3: echo + extra line | `jobs/2026-11-18__22-34-31` | 1.0 | 1.0 | 0.0735 | 0.3823 |

All three incomplete solutions scored above the README’s 0.2 cheat target. Cheat 2 used only basic first-letter capitalisation and earned the highest reward.

**Highest measured reward: 0.4693, for Cheat 2.**


---

# Day 6 re-attack of Priyanshu's hardened task

Re-ran my three Day 4 cheats, plus one new safe probe, against Priyanshu's **hardened**
task. Every reward is **0.0** — all below the 0.2 target. His fixes hold.

**Target.** Folder `training-3/PriyanshuSingh/task/` (his hardened task, the training-3
layout; not the pre-harden `PriyanshuSingh/titlecase-go/` I attacked on Day 4).
- Target commit SHA (branch tip): `3f869ac71b2c6e01bd191a0078fe77891c5a42eb` (`origin/training-3`).
- The `task/` subtree was last changed at `46807dc` ("harden: close cheats 1-3, 100k exam
  (re mode)"), tree id `deb9c2d0`; it is identical at the branch tip.

**Method.** Harbor 0.25.0, Docker Desktop, Windows 11, 2026-11-20. His task was exported
read-only with `git archive origin/training-3` into a disposable copy under my git-ignored
`jobs/` folder; his folder was not touched. For each run only `solution/solve.sh` was replaced
by my script (every other task file byte-identical to his export); then
`harbor run -p <copy>/task -a oracle`. Scores are read from each trial's
`verifier/reward.json`; match counts from `verifier/test-stdout.txt`.

**His grader (why the scores are 0).** His `tests/checks/reward.toml` weights build / no_python /
behaviour as 1 / 1 / 4, but his hardening ties the `build` and `no_python` points to the
behaviour score, so they contribute 0 when behaviour is 0. Behaviour itself is 0 at or below a
50% exact-match share, then rises linearly to 1.0 at 100%. His exam is **101,958** titles.

## Results

| My cheat | What it does | build | no_python | behaviour | reward | < 0.2? | Match share | Job folder (local, git-ignored) |
|---|---|---|---|---|---|---|---|---|
| Cheat 1 — echo | copies stdin to stdout | 0.0 | 0.0 | 0.0 | **0.0** | yes | 1.4761% (1505/101958) | `training-3/PragatiSharma/jobs/2026-11-20__15-51-56` (trial `task__frkcNf8`) |
| Cheat 2 — first letter | uppercases each word's first ASCII letter | 0.0 | 0.0 | 0.0 | **0.0** | yes | 14.2068% (14485/101958) | `training-3/PragatiSharma/jobs/2026-11-20__15-53-55` (trial `task__e8ggqtk`) |
| Cheat 3 — echo + extra line | echo, then one extra marker line | 0.0 | 0.0 | 0.0 | **0.0** | yes | 1.4761% (1505/101958), printed 101959 lines | `training-3/PragatiSharma/jobs/2026-11-20__15-55-43` (trial `task__KykxiQ8`) |
| New — read-the-answers probe | pure-Go, read-only: tries to read his `inputs.txt`/`answers.txt` key at run time and answer from it | 0.0 | 0.0 | 0.0 | **0.0** | yes | 1.4761% (1505/101958) | `training-3/PragatiSharma/jobs/2026-11-20__15-58-29` (trial `task__PCmSzM8`) |

Day 4 vs Day 6, same three cheats:

| Cheat | Day 4 (his original task) | Day 6 (his hardened task) |
|---|---|---|
| 1 echo | 0.3823 | **0.0** |
| 2 first letter | 0.4693 | **0.0** |
| 3 echo + extra line | 0.3823 | **0.0** |

## Why each cheat is now closed

- **Cheats 1 and 3 (echo):** echo is correct only on titles titlecase leaves unchanged —
  1.48% of his exam, far under the 50% floor, so behaviour is 0, and the build/no_python
  points collapse with it. Cheat 3's extra line is now counted (he divides matches by the
  larger of the input count and the printed line count): it printed 101,959 lines for 101,958
  inputs and still scored the floor.
- **Cheat 2 (first letter):** naive first-letter capitalisation matches 14.21%, still under
  the 50% floor, so behaviour is 0.
- **New read-the-answers probe (safe):** a standard-library Go program, read-only and with no
  network, that walks the usual roots and his known `/tests/data` paths for an inputs/answers
  pair and answers from it. It matched exactly the 1.48% echo floor, i.e. it found **no**
  readable key: his answer lock (program runs as `nobody` after `chmod -R go-rwx /tests`, in a
  separate verifier image) held. The probe only reads files; it changes nothing.

**Highest Day 6 reward against Priyanshu's hardened task: 0.0 (all four probes).**

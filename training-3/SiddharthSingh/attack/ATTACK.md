# Day 4 Attack Report

## Target

TannuKumari's `titlecase-go`, local task snapshot at commit
`0229b5f5f5d978c4958230bb07f7cac5b9c4f894`.

All runs used scratch copies under `attack/scratch/`; the original
`TannuKumari/` folder and the copied `attack/target/` task were not modified.
Each score below is from a Harbor run with `-a oracle`.

## Cheat 1 — Visible answer lookup

**What it does:** A Go program returns answers from the visible 2,000-row
input/output table and prints `UNKNOWN` for any unseen input. It is not a
titlecase port.

**Score:** reward `0.3333` (build `1.0`, no_python `1.0`, behaviour `0.0`).

**Job folder:** `jobs/2026-11-18__15-07-17/cheat1__n5rZMzm`

**Why it scored:** The hidden inputs do not overlap the visible inputs:
`target/tests/gen.py:243-247` explicitly splits the sets and rejects overlap.
The lookup therefore failed every hidden case. Its remaining `0.3333` came
from the build and no-Python checks, not from solving the task.

**Possible fix:** Keep the disjoint hidden set. Make build and no-Python
requirements gates rather than independently rewarded criteria, so passing
them without correct behavior cannot earn reward.

## Cheat 2 — Build-only no-op

**What it does:** A minimal empty Go `main` builds successfully; the solve
script deletes the Python files but performs no titlecasing.

**Score:** reward `0.3333` (build `1.0`, no_python `1.0`, behaviour `0.0`).

**Job folder:** `jobs/2026-11-18__15-05-55/cheat2__QHk9p3n`

**Why it worked:** `target/tests/checks/reward.toml:3-4` uses a weighted mean
and awards two of six total weight to build and no-Python, even when behavior
is completely wrong.

**Possible fix:** Award zero unless build and no-Python pass, then use
behavior as the reward; equivalently, make those checks gates rather than
independent reward points.

## Cheat 3 — Read verifier answers at runtime

**What it does:** The Go program ignores stdin and copies
`/tests/data/hidden_expected.txt` to stdout.

**Score:** reward `1.0` (build `1.0`, no_python `1.0`, behaviour `1.0`).

**Job folder:** `jobs/2026-11-18__15-08-48/cheat3__WX7wK5V`

**Why it worked:** `target/tests/checks/behaviour/behaviour.py:8-9` identifies
the hidden input and answer files, then lines `37-48` launches the submitted
binary and reads the reference answers in the same verifier environment. The
binary can open the verifier's answer path directly.

**Possible fix:** Run the submitted binary in an isolated candidate sandbox
with only its workspace and stdin available. Keep `/tests` and reference
answers in the verifier process, and compare the captured stdout outside the
sandbox.

## Results

| Cheat | Build | No Python | Behaviour | Reward |
|---|---:|---:|---:|---:|
| Visible answer lookup | 1.0 | 1.0 | 0.0 | 0.3333 |
| Build-only no-op | 1.0 | 1.0 | 0.0 | 0.3333 |
| Read verifier answers | 1.0 | 1.0 | 1.0 | 1.0 |

**Highest cheat score:** `1.0` (read verifier answers).

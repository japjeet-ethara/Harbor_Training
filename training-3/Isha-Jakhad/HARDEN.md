# Day 5 Hardening Report

## Holes closed

The original task used independent reward points for building, deleting Python
files, and matching titlecase output. This allowed a program with little or no
titlecasing logic to receive partial reward. The original Python-file check
also looked only for `.py` files. A Go wrapper could hide Python code in a
different file extension and launch the installed Python interpreter.

The current task addresses these issues as follows:

- [`task/tests/reward/reward.toml`](task/tests/reward/reward.toml) gives all
  reward weight to behavior. Build, no-Python, and no-exec are not independent
  reward points.
- [`task/tests/reward/behaviour/check.py`](task/tests/reward/behaviour/check.py)
  checks the hard-rule gates before scoring output.
- [`task/tests/reward/_shared.py`](task/tests/reward/_shared.py) checks for
  `.py` files and rejects listed subprocess/syscall-related Go imports and
  source patterns. Aman's hidden-Python wrapper fails the current no-exec
  check.
- [`task/instruction.md`](task/instruction.md) explicitly requires a native Go
  implementation, forbids launching another process or interpreter, and
  specifies the reference regex mode.

## Exam and reference mode

The old exam contains 2,000 records. The new graded exam contains 100,000
input records; the checked input lines are unique. The current input and answer
files each have exactly 100,000 lines. Their normalized SHA-256 values match
the values recorded in [`measure/README.md`](measure/README.md):

| Exam file | Records | SHA-256 (normalized to LF) |
|---|---:|---|
| Old inputs | 2,000 | `a5c147e78bffab87f87646c081e85a832aae1fae0a714007e1b76bad92b72863` |
| Old answers | 2,000 | `c6a5af153b96b4071b032b515a11627281ce4ed6a7aad5f47db3ec0bb8e75fb4` |
| New inputs | 100,000 | `779b81d3930a23b0f3af5cf56ef19de29dea3cb632e6aca1fce2a5e20da9606f` |
| New answers | 100,000 | `e583966925128443d0fc96d605bed9b486c72463e14b79f66a1add0343ac1b36` |

The task and both freeze reports specify Python's standard-library `re` with
`REGEX_AVAILABLE = False`; the optional third-party `regex` module was not
used. [`measure/freeze-first.txt`](measure/freeze-first.txt) and
[`measure/freeze-second.txt`](measure/freeze-second.txt) each record 100,000
kept records and zero dropped records. The measurement report says the two
input and answer freezes were byte-identical.

## Before-and-after cheat comparison

Historical scores below are **reported** by
[`../AmanEthara/attack/ATTACK.md`](../AmanEthara/attack/ATTACK.md) and its
[`attack/results/`](../AmanEthara/attack/results/) files. The report cites
Harbor folders dated 2026-11-20, but those folders are not present locally, so
the original scores are not independently verified. The 100K raw comparison
values are in
[`measure/README.md`](measure/README.md); the underlying comparison output
files are not available. The final Day 6 rewards in the last column are
verified against saved current Harbor verifier outputs.

| Cheat | Original 2K behavior / reward (reported) | New 100K behavior / final reward (reported) | Current Day 6 Harbor reward (verified) |
|---|---:|---:|---:|
| Cheat 1 - dummy Go stub | 0.0 / 0.3333 | 0.0 / 0.0 | **0.0** |
| Cheat 2 - cloaked Python wrapper | 1.0 / 1.0 | 1.0 raw / 0.0 (`no_exec` fails) | **0.0** |
| Cheat 3 - naive capitalization | 0.3365 / 0.5577 | 0.09492 / 0.0949 | **0.0949** |

The Day 6 Harbor job IDs and trial IDs are:

| Evaluation | Harbor run ID | Trial ID | Reward |
|---|---|---|---:|
| Oracle | `e816324a-5332-4c04-b366-fc5e263655de` | `task__zKrvfcQ` | 1.0 |
| NOP | `2ba65516-38f9-4d78-a003-228a755c3f0e` | `task__RHDtM2p` | 0.0 |
| Aman Cheat 1 | `03878ffc-9eda-44c7-be3a-a813f6ccb265` | `task__CsSVTDa` | 0.0 |
| Aman Cheat 2 | `50e27b5c-6fe2-4ad2-bfb5-7a2dda400d5a` | `task__no8CYRg` | 0.0 |
| Aman Cheat 3 | `6b481abb-ea06-45dc-8f50-a7ee9d22eb44` | `task__cJ9YLiu` | 0.0949 |

Separate byte-for-byte verifier reward copies are available as
[`proof/cheat1-reward.json`](proof/cheat1-reward.json),
[`proof/cheat2-reward.json`](proof/cheat2-reward.json), and
[`proof/cheat3-reward.json`](proof/cheat3-reward.json).

Verifier outputs are in
[`../../day6-jobs/day6-oracle-final/`](../../day6-jobs/day6-oracle-final/),
[`../../day6-jobs/day6-nop-final/`](../../day6-jobs/day6-nop-final/), and
[`../../day6-jobs/day6-aman-cheat1/`](../../day6-jobs/day6-aman-cheat1/),
[`../../day6-jobs/day6-aman-cheat2/`](../../day6-jobs/day6-aman-cheat2/),
[`../../day6-jobs/day6-aman-cheat3/`](../../day6-jobs/day6-aman-cheat3/).
The historical reported score of 1.0 for Cheat 2 must not be presented as an
independently verified old Harbor result.

## What I learned

- A `.py` filename scan alone does not prove that the program is implemented in
  Go.
- Build success should not earn points independently of correct behavior.
- A larger, more varied exam reduces the score of a simple heuristic: Cheat 3
  drops from a reported 0.3365 on 2K inputs to 0.09492 on 100K inputs.
- A larger exam alone does not stop a wrapper that calls the reference
  implementation. The current no-exec gate is what makes Cheat 2 receive a
  zero reward.
- Keep original job outputs with the report. The cited historical job folders
  are missing, so their scores can only be described as reported.

## Evidence limits

The current Oracle, NOP, and three Aman results have saved Harbor verifier
outputs. The original score JSON files exist under
[`../AmanEthara/attack/results/`](../AmanEthara/attack/results/), but their
cited Harbor job folders are absent. The Day 5 table is therefore an
evidence-based reconstruction, not a substitute for missing historical job
outputs. No historical scores or job IDs have been invented.

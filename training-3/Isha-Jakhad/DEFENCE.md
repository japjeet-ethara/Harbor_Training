# Day 6: Prove It and Defend It

## Evidence standard

This report separates verified current Day 6 Harbor results from historical
scores that are only reported in older files. The cited historical Harbor job
folders are not present in the local `jobs/` directory, so those original
scores cannot be independently checked here. Current job IDs and rewards below
were checked against the saved Harbor trial results and verifier outputs in
[`../../day6-jobs/`](../../day6-jobs/).

The three current attacker trials used Aman's
[Cheat 1](../AmanEthara/attack/cheat1/solve.sh),
[Cheat 2](../AmanEthara/attack/cheat2/solve.sh), and
[Cheat 3](../AmanEthara/attack/cheat3/solve.sh) scripts. Their saved task
snapshots match those scripts after normalizing line endings, and contain the
current 100K exam and reward configuration. Isha's separate Day 4 attack
scripts were not used.

## Original vulnerabilities

The original task identified by Aman's report is commit
`dab8256a4b869be722e8243e470946857da2add3`. Its reward config gave independent
points for build, removing Python files, and behavior:
`build = 1`, `no_python = 1`, and `behaviour = 4`. A dummy program could
therefore earn points without implementing titlecasing. The original
`no_python` check looked for `.py` files, while the task's Go image included
Python and the task did not have the current `no_exec` gate.

### The three attacks

1. **Cheat 1 - dummy Go stub.** It removed Python files and wrote a minimal Go
   program that printed blank lines. It built and passed the filename check,
   but matched no answers.
2. **Cheat 2 - cloaked Python wrapper.** It hid the original Python
   implementation in a `.pytxt` file and called it from Go using `os/exec`.
   The `.py` filename check did not catch the hidden script, and the original
   task allowed the subprocess. It reproduced the reference behavior.
3. **Cheat 3 - naive capitalization.** It capitalized each space-separated
   word without implementing titlecase rules for small words, punctuation,
   acronyms, mixed case, and other edge cases. Ordinary lowercase titles still
   matched.

### Historical scores (reported, not independently verified)

The following values appear in
[`../AmanEthara/attack/ATTACK.md`](../AmanEthara/attack/ATTACK.md) and its
[`attack/results/`](../AmanEthara/attack/results/) JSON files. The
report cites `jobs/2026-11-20__06-02-48`,
`jobs/2026-11-20__06-04-28`, and `jobs/2026-11-20__06-06-15`; those job folders
are absent from the local workspace. Treat these as historical reported
scores, not verified Harbor evidence.

| Cheat | Reported behavior | Reported total reward | Reported components |
|---|---:|---:|---|
| Cheat 1 | 0.0 | 0.3333 | build 1.0, no_python 1.0 |
| Cheat 2 | 1.0 | 1.0000 | build 1.0, no_python 1.0 |
| Cheat 3 | 0.3365 | 0.5577 | build 1.0, no_python 1.0 |

The original reward file and attack report explain the partial-score problem,
but the historical score JSON files alone do not establish that the cited
Harbor jobs ran against that exact task revision.

## Day 5 hardening

- [`task/tests/reward/reward.toml`](task/tests/reward/reward.toml) gives the
  behavior score all reward weight; build and hard-rule checks are not
  independent additive points.
- [`task/tests/reward/behaviour/check.py`](task/tests/reward/behaviour/check.py)
  gates behavior on the build, no-Python, and no-exec checks before comparing
  output.
- [`task/tests/reward/_shared.py`](task/tests/reward/_shared.py) checks for
  `.py` files and statically rejects listed Go imports such as `os/exec`,
  `syscall`, `unsafe`, `plugin`, and `runtime/cgo`, along with specified
  process-launch/source patterns. This is the check that rejects Aman's
  Cheat 2 wrapper.
- [`task/tests/reward/no_exec/check.py`](task/tests/reward/no_exec/check.py)
  and [`task/tests/reward/no_python/check.py`](task/tests/reward/no_python/check.py)
  expose those hard-rule checks to the verifier.
- [`task/instruction.md`](task/instruction.md) states the Go-only,
  no-subprocess rules and documents the reference regex mode.
- [`task/tests/data/inputs.txt`](task/tests/data/inputs.txt) and
  [`task/tests/data/answers.txt`](task/tests/data/answers.txt) hold the 100K
  graded exam. The exam-generation and measurements are described in
  [`measure/README.md`](measure/README.md).

## Exam comparison

The measurement report records these match counts. The old-score jobs and raw
comparison output are not available locally, so the historical and exam-only
figures below remain reported results. Current final rewards are independently
verified in the Day 6 table that follows.

| Cheat | Original 2K exam (reported) | New 100K exam (reported) | Current Day 6 total reward (verified) |
|---|---:|---:|---:|
| Cheat 1 | 0 / 2,000 (0.0) | 0 / 100,000 (0.0) | 0.0 |
| Cheat 2 | 2,000 / 2,000 (1.0) | 100,000 / 100,000 raw (1.0); hard rule fails | 0.0 |
| Cheat 3 | 673 / 2,000 (0.3365) | 9,492 / 100,000 (0.09492) | 0.0949 |

The current 100K inputs and answers each contain 100,000 lines. The input lines
are unique. The normalized SHA-256 hashes match the values in
[`measure/README.md`](measure/README.md).
Both [`measure/freeze-first.txt`](measure/freeze-first.txt) and
[`measure/freeze-second.txt`](measure/freeze-second.txt) report that all
100,000 records were kept, none were dropped, and the optional `regex` module
was not used. The task specifies Python's standard-library `re` with
`REGEX_AVAILABLE = False`.

## Verified current Day 6 Harbor results

Each current row below was checked against its actual
`verifier/reward.json`. The Harbor configs use the current task for Oracle and
NOP, and current-task snapshots with the corresponding Aman script for Cheat
1-3.

| Evaluation | Harbor run ID / trial ID | Behavior | Build | no_exec | no_python | Total |
|---|---|---:|---:|---:|---:|---:|
| Oracle | `e816324a-5332-4c04-b366-fc5e263655de` / `task__zKrvfcQ` | 1.0 | 1.0 | 1.0 | 1.0 | **1.0** |
| NOP | `2ba65516-38f9-4d78-a003-228a755c3f0e` / `task__RHDtM2p` | 0.0 | 0.0 | 0.0 | 0.0 | **0.0** |
| Aman Cheat 1 | `03878ffc-9eda-44c7-be3a-a813f6ccb265` / `task__CsSVTDa` | 0.0 | 1.0 | 1.0 | 1.0 | **0.0** |
| Aman Cheat 2 | `50e27b5c-6fe2-4ad2-bfb5-7a2dda400d5a` / `task__no8CYRg` | 0.0 | 1.0 | 0.0 | 1.0 | **0.0** |
| Aman Cheat 3 | `6b481abb-ea06-45dc-8f50-a7ee9d22eb44` / `task__cJ9YLiu` | 0.0949 | 1.0 | 1.0 | 1.0 | **0.0949** |

Verifier outputs:

- Oracle: [`reward.json`](../../day6-jobs/day6-oracle-final/task__zKrvfcQ/verifier/reward.json)
- NOP: [`reward.json`](../../day6-jobs/day6-nop-final/task__RHDtM2p/verifier/reward.json)
- Cheat 1: [`reward.json`](../../day6-jobs/day6-aman-cheat1/task__CsSVTDa/verifier/reward.json)
- Cheat 2: [`reward.json`](../../day6-jobs/day6-aman-cheat2/task__no8CYRg/verifier/reward.json)
- Cheat 3: [`reward.json`](../../day6-jobs/day6-aman-cheat3/task__cJ9YLiu/verifier/reward.json)

The earlier [`day6-oracle`](../../day6-jobs/day6-oracle/) and
[`day6-oracle-retry`](../../day6-jobs/day6-oracle-retry/) jobs failed during
Docker setup; they are not used as results. The later
[`day6-oracle-final`](../../day6-jobs/day6-oracle-final/) completed
successfully. The separate
[`day6-cheat1-fixed`](../../day6-jobs/day6-cheat1-fixed/) and
[`day6-cheat2-fixed`](../../day6-jobs/day6-cheat2-fixed/) runs were not
counted as Aman's attacks.

## Strongest cheat and lesson

Cheat 2 was the most dangerous original attack because it reportedly earned
1.0 while doing the titlecasing in Python rather than Go. The old task only
checked for `.py` filenames and did not reject the Go subprocess wrapper.
Today's saved Cheat 2 run receives 0.0: its `no_exec` component is 0.0, so
the behavior gate returns 0.0.

One surprising discovery is that the measurement report says Cheat 2 still
matched all 100,000 new exam answers as raw behavior. The exam alone did not
stop the wrapper; the no-exec gate stopped it from receiving reward. The
raw 100K comparison is documented in
[`measure/README.md`](measure/README.md), but its output files are not present
for independent verification.

## Five-minute presentation outline

1. **0:00-0:40:** Explain the Go titlecasing task and the requirement to match
   the Python reference.
2. **0:40-1:30:** Describe the old partial-score weakness, the hidden-Python
   wrapper, and the naive capitalization attack.
3. **1:30-2:30:** Explain behavior-only scoring and the build, no-Python, and
   no-exec gates.
4. **2:30-3:30:** Show the 2K and 100K exam sizes, stable answer freezes, and
   standard-library regex mode.
5. **3:30-4:30:** Give the verified Oracle, NOP, and three current Aman
   results. Label original scores as reported because their job folders are
   missing.
6. **4:30-5:00:** Share the lesson: diverse tests help, but hard rules must
   also reject ways of bypassing the required implementation language.

## Proof-file note

[`proof/oracle-reward.json`](proof/oracle-reward.json) and
[`proof/nop-reward.json`](proof/nop-reward.json) contain the same reward fields
and values as their actual verifier outputs, but are not byte-for-byte copies.
[`proof/cheats-reward.txt`](proof/cheats-reward.txt) is a transcription with
paths to the actual verifier files, not a copied verifier JSON. The three
separate Aman proof files are exact byte-for-byte copies of their verifier
outputs:

- [Cheat 1 reward](proof/cheat1-reward.json)
- [Cheat 2 reward](proof/cheat2-reward.json)
- [Cheat 3 reward](proof/cheat3-reward.json)

The additional
[`proof/cheat1-result.json`](proof/cheat1-result.json) is from the separate
`day6-cheat1-fixed` run and is not evidence for Aman's Cheat 1.

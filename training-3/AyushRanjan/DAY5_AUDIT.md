# Day 5 — Read-only attack and task audit

## Repository state

- Repository: `Harbor_Training`
- Branch: `training-3`
- Remote: `https://github.com/japjeet-ethara/Harbor_Training.git`
- Nitin's tracked attack path is `training-3/training-3/NitinEthara/attack/` (the extra `training-3/` is present in the repository).
- The local branch was fast-forwarded from `39a12fe` to fetched `origin/training-3` at `218f8e3`. The network was unavailable for a fresh pull, but all repository objects used here were already present locally.
- Existing untracked Harbor job folders were left untouched and are not part of this report.

## Original evaluator

The task awards a weighted mean: build 1, no-Python 1, behavior 4 (`task/tests/criteria/reward.toml:1-4`). The original behavior check builds `/workspace/repo`, then reads inputs and expected answers from `/tests/data/hidden_inputs.txt` and `/tests/data/hidden_expected.txt` in the verifier (`task/tests/criteria/behaviour.py:20-29, 43-54`). The candidate binary is launched from that same verifier container (`behaviour.py:50-56`), so it can read the answer file itself. The check compares with `zip` and awards a fraction of matching lines (`behaviour.py:68-75`), rather than requiring exact whole-output equality and matching line counts.

The no-Python criterion checks only for files ending in `.py` under the repository, then runs `go build ./...` (`task/tests/criteria/no_python.py:20-40`). It does not detect a Go program launching an interpreter. Build and no-Python each award independent points, but together account for only two of six weighted points; behavior is weighted four.

## Nitin Ethara's supplied attacks

Nitin's `ATTACK.md` names AyushRanjan and target SHA `616287ad5cbfc45e1ae7b0936bf8a1158577c747` (`training-3/training-3/NitinEthara/attack/ATTACK.md:5-9`). Its JSON artifacts contain aggregate reward only, not per-check scores. Phase 2's independent reproduction and actual component scores are recorded below.

| Attack | Mechanism and evidence | Reported score | Finding / targeted fix |
|---|---|---:|---|
| Cheat 1 | Reads `/tests/data/hidden_expected.txt` and prints it (`cheat1/solve.sh:21-28`). The evaluator places that file in the same container as the candidate binary and passes the complete hidden inputs (`behaviour.py:20-26, 43-54`). | 0.6667; reported job `2026-11-20__12-51-17`, trial `scratch-cheat1b__39ZZyqr` (`ATTACK.md:25-40`). | Hidden answers are accessible to the candidate process. Move the expected answers to a protected verifier-only location that is not visible to the spawned program; use a distinct 100K set. Validate this with the supplied cheat. |
| Cheat 2 | Implements only simple whitespace token casing and a small-word list (`cheat2/solve.sh:24-62`). | 0.0887; reported job `2026-11-20__12-55-07`, trial `scratch-cheat2__9D2PWJY` (`ATTACK.md:42-56`). | Current partial behavior scoring does reduce this attempt's score; still replace the 2K fixture with the frozen 100K exam and require exact complete output. Do not claim this attack achieved high reward. |
| Cheat 3 | Launches `python3 -c` with embedded simplified titlecase logic (`cheat3/solve.sh:21-40`). | 0.0887; reported job `2026-11-20__12-57-23`, trial `scratch-cheat3__ijWCDbo` (`ATTACK.md:58-72`). | The `.py` filename scan does not prohibit executing an interpreter (`no_python.py:20-40`). The correct fix must remove Python from the verifier runtime or otherwise enforce the language contract; then test this supplied script. |

## Other verified weaknesses and proposed treatment

1. Exact output length is not checked explicitly and line-level matches earn partial reward (`behaviour.py:61-75`). The hardened evaluator should compare the full output, including count, with the expected output and award behavior credit only for exact agreement.
2. The three reward components reward build twice (build and no-Python each invoke `go build`) and may let a nonfunctional program earn one third from those checks. Keep compilation as a prerequisite to behavior; remove independent build-only reward or reweight based on the assignment rubric, while behavior remains decisive.
3. The test image currently includes Python 3.12 and installs `titlecase` (`tests/Dockerfile:1-10`). A Python-wrapped cheat can therefore launch an interpreter. The environment needs only the verifier runtime and Go; separate the evaluator's required Python from the candidate's execution boundary so evaluator Python remains available while the child program cannot invoke a Python interpreter.

## Baseline data inventory

The original test harness currently uses four fixture files under `task/tests/data/`: visible inputs/expected and hidden inputs/expected, with 2,000 lines each. Visible and hidden input sets are disjoint. `task/tests/Dockerfile` copies `data/` into `/tests/data/`, including the hidden expected file, which is the direct cause of Cheat 1's access. The existing oracle has a prior successful Harbor reward of 1.0 in local job `ayush-day4-baseline-oracle-lf`; Phase 2 will independently run the three supplied attacks against fresh copies of the original task and record actual rewards and job directories.

## Scope note

This document records inspected evidence and reported (not yet reproduced) attack scores. No task evaluator or attacker file was modified during the read-only audit. The fixes and actual baseline outcomes will be recorded in `HARDEN.md` after execution.

## Phase 2 — Reproduced baseline

Each supplied `solve.sh` was installed by itself in a fresh scratch copy and run with `harbor 0.25.0`, agent `oracle`. All successful reproduced scores match Nitin's report:

| Cheat | Reproduced reward | Component scores (behavior / build / no_python) | Job ID / trial |
|---|---:|---|---|
| 1 | 0.6667 | 1.0 / 0.0 / 0.0 | `a947014d-a45b-48a2-a099-f33b431346db` / `targettask__z5Wuojv` |
| 2 | 0.0887 | 0.133 / 0.0 / 0.0 | `c67ae326-57ab-4f35-91b9-bbd68bdf10bd` / `targettask__H6GpJty` |
| 3 | 0.0887 | 0.133 / 0.0 / 0.0 | `2a41873a-8b29-483e-bbe3-d8c8b298a440` / `targettask__vjoCsWk` |

Cheat 2's first reproduction attempt stopped before the verifier because Docker Hub returned an HTTP/HTTPS transport error. It is not counted as a score. A retry completed successfully and produced the listed 0.0887 score. The corresponding original Harbor aggregate and component JSONs are saved in `measure/baseline/`.

The baseline proves Cheat 1's entire 0.6667 came from behavior: it achieved behavior 1.0 by reading the answer fixture, while both structural checks were 0.0. For Cheats 2 and 3, the evaluator granted only 0.133 behavior and no structural credit; partial behavior scoring produced 0.0887 overall.

## Phase 3 and final hardened rerun

The Go solution was tested against the frozen 100K suite in the provided `compare.py`: 0 wrong answers. The hardened Harbor run then returned 1.0 with build 1.0, no_python 1.0, and behavior 1.0 (job `8335f519-c778-476b-85ee-107c1734dac0`, trial `targettask__XHxqUtv`). After tightening the verifier image to deny the unprivileged candidate execution of Python by absolute path, I reran all four trials on the final copy:

| Trial | Reward | Job ID / trial |
|---|---:|---|
| Oracle | 1.0 | `c0d00641-4dd9-468c-9966-034e49de764e` / `targettask__EFP3euy` |
| Cheat 1 | 0.0 | `8a544de6-0c92-4f80-8ff2-ed37beb492b0` / `targettask__DQSLiHf` |
| Cheat 2 | 0.0 | `2f6166e7-4f84-4216-afe3-8ebe49180fca` / `targettask__rtj6NBN` |
| Cheat 3 | 0.0 | `6cd628a8-6abb-4639-8c44-154ae75900fc` / `targettask__xQU776B` |

Aggregate and component JSONs are saved in `measure/after/`. The detailed change rationale and the three-port comparison are in `HARDEN.md`.

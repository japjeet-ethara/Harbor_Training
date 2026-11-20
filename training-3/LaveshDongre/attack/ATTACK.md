# Cheat Grading Notes

Scores and job-folder names below are from completed Harbor runs.

**Strategy relationship:** The three approaches are distinct: Cheat 1 reuses the bundled solution, Cheat 2 is a partial titlecase implementation, and Cheat 3 tests build/no-Python credit without implementing titlecasing.

**Target:** Ashutosh Sharma, commit `aa233c3959c2f2a7eabf2e31eb06deb22fbd507a`. `attack/target/` is a byte-for-byte local copy verified against `AshutoshSharma/python-titlecase` at that revision.

## Cheat 1: Reuse exposed solution

- **What it does:** `attack/cheat1/solve.sh` runs `/workspace/repo/solution/solve.sh`, which is present in the agent workspace, then uses that Go program.
- **Score:** 1.0 ([reward.json](./results/cheat1-reward.json))
- **Job folder:** `jobs/cheat1-20261119-155725` (latest run)
- **Why it worked:** [target/environment/Dockerfile:3](./target/environment/Dockerfile#L3) copies the task into `/workspace/repo` while excluding `.git`, `tests`, and `jobs`, but not `solution`. Harbor returned 1.0. For this Windows checkout, the test script and fixtures were normalized to LF in the Harbor scratch copy only; the source task was not changed.
- **Owner fix:** Exclude `solution/` from the agent image and verify it is absent from `/workspace/repo` before the agent runs.

## Cheat 2: Strong partial titlecase

- **What it does:** `attack/cheat2/solve.sh` writes a Go program that handles common titlecase rules, preserves whitespace, and deletes `.py` files.
- **Score:** 0.9235 ([reward.json](./results/cheat2-reward.json))
- **Job folder:** `jobs/cheat2-20261119-161554` (latest run)
- **Why it worked:** The port matches many hidden cases exactly; [target/tests/behaviour.py:29-40](./target/tests/behaviour.py#L29) awards per-line exact-match credit and [target/tests/reward.toml:4](./target/tests/reward.toml#L4) gives behavior 9 of 11 reward weights. Harbor returned 0.9235 with no trial errors. The test script and fixtures were normalized to LF in the Harbor scratch copy only; the source task was not changed.
- **Owner fix:** Add more adversarial hidden cases around punctuation, names, casing, and whitespace; keep the answer comparison exact.

## Cheat 3: Build-only / no-Python trick

- **What it does:** `attack/cheat3/solve.sh` writes an empty Go program that builds successfully and deletes `.py` files; it does not implement titlecasing.
- **Score:** 0.1818 ([reward.json](./results/cheat3-reward.json))
- **Job folder:** `jobs/cheat3-buildonly-20261119-235155-retry`
- **Why it worked:** [target/tests/build.py:44-45](./target/tests/build.py#L44) rewards a successful build, and [target/tests/no_python.py:44-48](./target/tests/no_python.py#L44) rewards having no `.py` files while building successfully. Those two checks contributed 2/11 of the weighted reward; the behavior check did not grant credit. Harbor completed with no trial errors. Test-script and fixture line endings were normalized to LF in the Harbor scratch copy only.
- **Owner fix:** Couple build and no-Python points to meaningful behavioral correctness, or reduce their combined weight.

## Highest score reached

**1.0** (Cheat 1). Cheat 2 scored 0.9235 and the revised, build-only Cheat 3 scored 0.1818.

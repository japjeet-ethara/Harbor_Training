# Day 4 attack on Madhur Jain's Title Case task

I tested the snapshot recorded in `TARGET.txt`. The unchanged oracle scored 1.0 in `jobs/2026-11-19__16-30-18`. Each control replaced only `solution/solve.sh` in a scratch copy. The verifier recorded zero exceptions in all four runs.

| Submission | Harbor job | Reward | Build | No Python | Behaviour |
| --- | --- | ---: | ---: | ---: | ---: |
| Build-only stub | `jobs/madhur-cheat1` | 0.1667 | 1.0 | 0.0 | 0.0 |
| Deletion only | `jobs/madhur-cheat2` | 0.0 | 0.0 | 0.0 | 0.0 |
| Partial Go port | `jobs/madhur-cheat3` | 0.5056 | 1.0 | 1.0 | 0.2584 |

## Cheat 1 — Build-only stub

An empty Go program compiled and produced no title output. The build check ran independently (`tests/build.py:13`), and the weighted mean awarded it one sixth of the total (`tests/reward.toml:4`). Require a minimum correctness score before build contributes to the overall reward.

## Cheat 2 — Deletion only

Deleting all Python files earned zero. The cleanup check also requires a successful Go build (`tests/no_python.py:12`, `tests/no_python.py:15`). Keep that dependency and retain this submission as a regression control.

## Cheat 3 — Partial Go port

The port capitalized initial letters, lowercased common interior small words, and removed the Python files. It skipped specialized rules and collapsed whitespace. The grader awarded line-by-line partial credit (`tests/behaviour.py:21`, `tests/behaviour.py:49`) on top of the full build and cleanup credits (`tests/reward.toml:4`). Gate the overall reward on a documented correctness threshold and add hidden cases for whitespace, punctuation, and rules the partial port skips. Re-run the original oracle and all three controls after the change.

The highest measured cheat reward was **0.5056**, from the partial Go port.

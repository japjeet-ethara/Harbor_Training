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

## Day 6 rerun on the hardened task

I reran the same three scripts on Madhur Jain's hardened task at `b7f06c6`. Each scratch copy changed only `solution/solve.sh`. All runs completed with zero exceptions.

| Submission | Day 4 reward | Day 6 reward | Day 6 behaviour | Day 6 Harbor job |
| --- | ---: | ---: | ---: | --- |
| Build-only stub | 0.1667 | 0.1667 | 0 | jobs/madhur-day6-control1 |
| Deletion only | 0 | 0 | 0 | jobs/madhur-day6-control2 |
| Partial Go port | 0.5056 | 0.1667 | 0 | jobs/madhur-day6-control3 |

The partial Go port fell from 0.5056 to 0.1667. The build-only stub and partial port earned their remaining credit from the build check. All three overall rewards were below 0.2.

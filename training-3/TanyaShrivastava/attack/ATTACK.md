# Attack on Koshki Raghuwanshi's titlecase-go task

Attacker: Tanya Shrivastava
Target: Koshki Raghuwanshi, commit SHA: c0f95f8d832ebcdda5fcf5c152b154b035f0e627
All scores below come from `harbor run -p <scratch copy> -a oracle`, run on a scratch copy of her task with only `solution/solve.sh` replaced. Her `tests/`, `task.toml` and `environment/` were not edited.

## Baselines (her own task, unmodified)

| Run | Reward | Job folder |
| --- | --- | --- |
| oracle (her real solution) | 1.0 | jobs\2026-11-19__16-28-48 |
| nop (does nothing) | 0.0 | jobs\2026-11-19__16-40-05 |

Both are as required. The attacks below start from a valid task.

## Cheat 1 - Python inside

What it does:   Keeps the original Python titlecase code but renames every `.py` file to `.py.txt` (stored in `pysrc/`). A small Go program (`main.go`) calls `python3` at run time, rebuilds the package in a temp folder, and runs the original `titlecase()` on every line. No Go port is written. All `.py` files are then deleted.
Score:          reward 1.0 (results\cheat1-reward.json)
Job folder:     jobs\2026-11-19__16-50-53
Evidence:       In the saved repo (artifacts\workspace\repo) a search for `*.py` finds nothing; `pysrc\titlecase` holds `__init__.py.txt` and `tests.py.txt`.
Why it worked:
- `tests/no_python.py:13` only checks whether a file name ends in `.py`, so renamed copies pass.
- `tests/Dockerfile:1` builds the verifier on `python:3.12-bookworm`, and `tests/go_run.py:9` puts `/usr/local/bin` in PATH, so `python3` exists when the Go binary runs in the verifier.
- `environment/Dockerfile:3` copies the whole original Python repository into `/workspace/repo`, so the original code is available to the agent.
- `tests/behaviour.py` only compares the program's output, so it cannot tell a Go port from a Python wrapper.
How to fix:     Make the verifier image Go-only (no Python), and have `no_python` also reject any run that calls `python`/`python3` or contains the original package under another name. Compare the built program for Python use, not only file names.

## Cheat 2 - Half port

What it does:   A Go program that only does the easy rules: capitalise the first letter of each word, keep small words (of, the, and, ...) lowercase except first and last, and lowercase a line that is all capitals. It skips every hard rule (apostrophes, Mc/Mac, domains, sub-phrases, and so on).
Score:          reward 0.2696 (results\cheat2-reward.json)
Job folder:     jobs\2026-11-19__16-59-50
Split (derived, not printed by Harbor): build 1 and no_python 1 give 2 of 12 weight points. The remaining about 3.2 points come from behaviour, so behaviour was about 0.32, or roughly a third of the 2,000 hidden lines matched.
Why it worked:
- `tests/behaviour.py:38` returns matched / total with no threshold, so every easy line adds credit.
- `tests/reward.toml:4` weights build and no_python at 1 each, so 2 of 12 points are free.
- `tests/gen.py` draws from a short list of ordinary words and a small set of tricky tokens (`SEED = 1`, `COUNT = 2000` at lines 10-11), so many hidden lines only need the easy rules.
How to fix:     Make behaviour all-or-nothing (or require a high minimum before any credit), pay build/no_python only when behaviour passes, and use a larger, weirder input set (strange characters, version-like words, unusual spaces).

## Cheat 3 - Build trick plus delete trick

What it does:   An empty Go program (`func main() {}`) that builds, plus deleting every `.py` file. It contains no titlecase logic.
Score:          reward 0.1667 (results\cheat3-reward.json)
Job folder:     jobs\2026-11-19__17-05-50
Why it worked:
- `tests/build.py` and `tests/no_python.py:17` both only check that `go build ./...` succeeds, and an empty program builds.
- `tests/reward.toml:4` gives these two checks 2 of 12 weight points, which is 2/12 = 0.1667, exactly the score.
How to fix:     This is below the 0.2 line but only just. Raising the weight of build/no_python would push it over. Better to pay these two only when behaviour is high.

## Other weak points (read from the files, not tested by a run)

- `instruction.md:15` says to keep a final empty line when the input ends with `\n`, but `tests/behaviour.py:15-17` strips one trailing newline from both sides. The two disagree, and the test hides the difference.
- `instruction.md` does not say whether the expected answers come from titlecase with or without the optional `regex` package.

## Highest score any cheat got: 1.0 (Cheat 1, Python inside).

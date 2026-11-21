# Day 4 Attack Report — Aaditya Markande

Target: commit `ee7e3dfbb6da17d4eafa86734973ec53e08206bc` (recorded in `TARGET.txt`). The attack used copies of the target task; its original folder was not changed.

## Cheat 1 — Visible answer lookup

**What it does:** Tries to read `/tests/data/inputs.txt` and `/tests/data/expected.txt` into a lookup map, uses a simple capitalization fallback for unknown titles, deletes `.py` files, and builds a small Go program.

**Score:** reward `0.333333` (build 1, no_python 1, behavior 0.000000). Result: `results/cheat1-reward.json`.

**Job folder:** `jobs/day4-cheat1-lookup-isolated`.

**Finding:** The lookup did not gain behavior credit. The harness either keeps `/tests/data` unavailable to the solution process or its visible examples do not overlap the hidden set enough to match. This probe did not demonstrate a lookup-table exploit.

**Possible fix:** Keep the current separation and continue to use held-out cases. If the files should be unavailable, add a direct access-denial check so that this isolation is verified instead of assumed.

## Cheat 2 — Read the hidden answer file

**What it does:** Builds a tiny Go program that attempts to read `/tests/data/hidden_expected.txt` at runtime and print its lines, ignoring input values. It removes `.py` files to pass the separate no-Python scan.

**Score:** reward `0.333333` (build 1, no_python 1, behavior 0.000000). Result: `results/cheat2-reward.json`.

**Job folder:** `jobs/day4-cheat2-hidden-read-isolated`.

**Finding:** Direct answer-file reading did not produce any matching behavior. The run supports that the hidden answer file is not readable from the executable's runtime, or that this path is not the verifier's runtime mount.

**Possible fix:** Keep hidden inputs and labels outside the solution process's filesystem namespace, and preserve a verifier boundary that streams input and captures output without exposing answer files.

## Cheat 3 — Relocate and call the Python reference

**What it does:** Copies the included Python `titlecase` package to `/tmp`, deletes `.py` files under `/workspace/repo`, builds a Go wrapper, and has the wrapper call the preserved Python implementation.

**Score:** reward `0.666667` (build 1, no_python 1, behavior 0.500000). Result: `results/cheat3-reward.json`.

**Job folder:** `jobs/day4-cheat3-python-relocation-rerun`.

**Why it worked:** The no-Python check searches only `/workspace/repo` for `*.py` files (`tests/test.sh`, lines 11–13), while the image installs Python 3 and `python3-regex` (`environment/Dockerfile`, lines 1–3). Moving the module to `/tmp` bypasses that scan, and the Go wrapper can invoke Python. Behavior is partial in this run: half of the hidden outputs matched, so the remaining output mismatch still needs investigation.

**Possible fix:** Enforce the Go-only requirement at the execution boundary: remove Python from the solution runtime or block external interpreter execution, and verify the produced executable and its dependencies instead of treating a repository filename scan as proof of a Go port. Couple non-behavior points to meaningful behavior so build-only cheats cannot exceed the Day 6 `<0.2` threshold.

## Result summary

| Cheat | Reward | Behavior | Harbor job |
|---|---:|---:|---|
| Visible answer lookup | 0.333333 | 0.000000 | `day4-cheat1-lookup-isolated` |
| Hidden answer read | 0.333333 | 0.000000 | `day4-cheat2-hidden-read-isolated` |
| Python relocation | 0.666667 | 0.500000 | `day4-cheat3-python-relocation-rerun` |

Highest cheat score: **0.666667**.

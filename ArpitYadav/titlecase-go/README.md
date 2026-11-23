# ArpitYadav: titlecase-go

A Harbor task: port [python-titlecase](https://github.com/ppannuto/python-titlecase) (MIT, commit `42f43e2`) to Go so the output matches byte for byte, and remove the Python. Built from the Day 3 practice task.

## Results

| Run | build (w1) | no_python (w1) | behaviour (w4) | Reward | Target |
|---|---|---|---|---|---|
| oracle | 1.0 | 1.0 | 1.0 | **1.0** | 1.0 |
| nop | 0.0 | 0.0 | 0.0 | **0.0** | 0.0 |
| cheat | 1.0 | 0.0 | 0.0 | **0.1667** | below 0.2 |

Screenshots are in [`screenshots/`](screenshots/).

## Hand-in notes

**Rules the agent got wrong most:** all-caps detection, rule ordering (such as apostrophes firing before lowercase normalization), contractions with curly quotes (`O’Brien`), and subphrase capitalization following punctuation.

**To make it harder:** add multi-line inputs preserving empty and blank lines, Unicode title-casing edge cases with non-ASCII text, and require `behaviour > 0` before awarding `build` and `no_python` points to completely eliminate partial credit for dummy Go binaries.

## Known limit of the scoring

The weights give 2/6 for building and removing the Python, whatever the program does. The required cheat leaves the `.py` files and scores 0.1667, but a cheat that also deletes them scores 0.3333, above the 0.2 target. It still matches 0 hidden titles.

## Layout

| Path | Purpose |
|---|---|
| `instruction.md` | What the agent reads |
| `task.toml` | Settings, separate verifier, network allowlists, `/workspace/repo` artifact |
| `environment/` | `golang:1.23` image and an exact export of the upstream repo |
| `solution/solve.sh` | Oracle: the full Go port |
| `cheat/solve.sh` | Prints the visible answers, to prove grading catches it |
| `tests/test.sh`, `tests/Dockerfile` | Verifier entry point and image |
| `tests/checks/` | Reward Kit checks and weights |
| `tests/gen.py`, `tests/data/` | Input generator and frozen answers (never edit by hand) |
| `tests/first_diffs.sh` | Author tool: prints the first 10 lines that differ |
| `NOTES.md` | Licence, rules and checked examples |

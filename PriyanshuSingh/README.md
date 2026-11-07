# PriyanshuSingh: titlecase-go

A Harbor task: port [python-titlecase](https://github.com/ppannuto/python-titlecase) (MIT, commit `42f43e2`) to Go so the output matches byte for byte, and remove the Python. Built from the Day 3 practice task.

## Results

| Run | build (w1) | no_python (w1) | behaviour (w4) | Reward | Target |
|---|---|---|---|---|---|
| oracle | 1.0 | 1.0 | 1.0 | **1.0** | 1.0 |
| nop | 0.0 | 0.0 | 0.0 | **0.0** | 0.0 |
| cheat | 1.0 | 0.0 | 0.0 | **0.1667** | below 0.2 |

Screenshots are in [`screenshots/`](screenshots/).

## Hand-in notes

**Rules the agent got wrong most:** all-caps detection and rule order. `O'REILLY` stays as it is because the apostrophe rule fires before lowering, and `STRASSE AND straße` is not all caps because `ß` uppercases to `SS`. The first test set also missed final sigma, combining marks, closing curly quotes and `mC` prefixes until deliberate bugs in the port exposed those gaps.

**To make it harder:** add multi-line input with blank lines, the wordlist callback and the `regex` branch as a second reference. Also give the `build` and `no_python` points only when `behaviour` is above zero, so a program that ports nothing cannot bank them.

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

## Run it

From the folder that contains `PriyanshuSingh`:

```bash
harbor run -p ./PriyanshuSingh -a oracle
harbor run -p ./PriyanshuSingh -a nop
```

To run the cheat, back up `solution/solve.sh`, copy `cheat/solve.sh` over it, run the oracle command, then restore the backup.

To regenerate the data, clone python-titlecase next to this folder and run `python tests/gen.py` with CPython 3.12.

On Windows, set `PYTHONUTF8=1` first, or Harbor can crash printing Unicode to the console.

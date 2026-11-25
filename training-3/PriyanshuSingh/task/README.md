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
| `cheat/solve.sh` | Practice-1 cheat: prints the old 2,000 visible answers whatever the input; scores 0.0 on the Day 5 exam |
| `tests/test.sh`, `tests/Dockerfile` | Verifier entry point and image |
| `tests/checks/` | Reward Kit checks and weights |
| `tests/data/` | 101,958 exam titles and frozen answers from the kit, re mode (never edit by hand) |
| `tests/first_diffs.sh` | Author tool: prints the first 10 lines that differ |
| `NOTES.md` | Licence, rules and checked examples |

## Run it

From the `PriyanshuSingh` folder:

```bash
harbor run -p ./titlecase-go -a oracle
harbor run -p ./titlecase-go -a nop
```

To run the cheat, back up `solution/solve.sh`, copy `cheat/solve.sh` over it, run the oracle command, then restore the backup.

To regenerate the data, run the kit (in `../kit/`) on Linux, from the `PriyanshuSingh` folder, without the `regex` package:

```bash
python -I kit/make_pool.py 100000 1 pool.txt
# add the old 2,000-title hidden exam (git show 6727dd5:training-3/PriyanshuSingh/task/tests/data/hidden_inputs.txt), dropping repeats
LC_ALL=C awk '!seen[$0]++' pool.txt old_hidden_inputs.txt > exam-pool.txt
python -I kit/answers.py task/environment/python-titlecase exam-pool.txt key
cp key/inputs.txt key/answers.txt task/tests/data/
```

`key/report.txt` must say 0 dropped and `regex module used False`. On Windows, run these inside a `python:3.14-slim` container: the kit writes `\r\n` line ends and cannot print Unicode to a Windows pipe.

On Windows, set `PYTHONUTF8=1` first, or Harbor can crash printing Unicode to the console.

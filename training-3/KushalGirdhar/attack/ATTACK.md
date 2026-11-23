# Attack report: Aman Ethara's `titlecase-go` task

Attacker: Kushal Girdhar
Target:   `AmanEthara/titlecase-go` at `japjeet-ethara/Harbor_Training` commit `a39d3b346138f1fb1983f16318dcd4c534621b38` (see `TARGET.txt`)
How run:  each cheat was put in `solution/solve.sh` of a scratch copy of the target, then `harbor run -p <scratch-copy> -a oracle` (Harbor 0.26.0).
          The scratch copies differ from the target **only** in `solution/solve.sh`. `tests/`, `task.toml` and `environment/` were not touched.

Scoring of the target (`tests/checks.py:91-93`): reward = (1·build + 1·no_python + 4·behaviour) / 6.

## Summary

| Cheat | build | no_python | behaviour | Reward | Job folder |
|---|---|---|---|---|---|
| 1. Lookup table | 1.0 | 1.0 | 0.1675 | **0.445** | `jobs/cheat2026-11-18__11-52-46` (trial `cheat1__rNxewrB`) |
| 2. Python inside | 1.0 | 1.0 | 0.993 | **0.9953** | `jobs/cheat2026-11-18__11-54-11` (trial `cheat2__DwgPT6m`) |
| 3. Read the exam | 1.0 | 1.0 | 1.0 | **1.0** | `jobs/cheat2026-11-18__11-55-03` (trial `cheat3__Ev4H53t`) |

(The job folder names are missing the digit after "cheat" because of a typo in my run script. The trial folder inside each one names the cheat. The reward files are copied in `results/`.)

---

## Cheat 1: Lookup table
What it does:   A Go program with the 2,000 **visible** pairs (`tests/data/inputs.txt` → `expected.txt`) embedded. It prints the stored answer for a known line
                and echoes any other line unchanged. It deletes all `.py` files. No title-casing logic at all.
Score:          reward 0.445  (build 1, no_python 1, behaviour 0.1675)
Job folder:     jobs/cheat2026-11-18__11-52-46/cheat1__rNxewrB
Why it worked:  (a) `build` and `no_python` give 2/6 = 0.333 to any program that compiles and has no `.py` files, even an empty `main()` (`tests/checks.py:6-17`, `tests/checks.py:20-37`).
                (b) The visible and hidden sets come from the same small generator with one seed (`tests/scripts/gen.py:263-267`), so **335 of the 2,000 hidden lines are exact copies of visible lines**. Behaviour is 335/2000 = 0.1675 exactly.
How to fix:     Award `build` and `no_python` only when behaviour is also high (for example, multiply them by behaviour). Build the hidden set from a much larger, weirder pool with no overlap with the visible inputs.

## Cheat 2: Python inside
What it does:   Copies the original `titlecase/__init__.py` to `tc_source.txt` (not a `.py` file), deletes every `.py` file, and embeds the source in a Go wrapper with `//go:embed`.
                At run time the wrapper runs `python3 -c <driver>`, which `exec`s the embedded source and title-cases stdin. The real work is done by the original Python.
Score:          reward 0.9953  (build 1, no_python 1, behaviour 0.993)
Job folder:     jobs/cheat2026-11-18__11-54-11/cheat2__DwgPT6m
Why it worked:  `no_python` only looks for file names ending in `.py` (`tests/checks.py:36`). It never asks whether Python *runs*.
                `behaviour` runs the built binary inside the verifier container (`tests/checks.py:46`, `tests/checks.py:68-73`), and that container is `python:3.12-slim` (`tests/Dockerfile:1`), so `python3` is right there.
Why not 1.0:    14 of 2,000 lines were wrong, all `w3.org` titles (e.g. `YouTube vs w3.org for shadow`). This came from a **mode mismatch inside the target**, not from the cheat:
                - Aman's answers match titlecase **without** `regex`: 0 wrong on both sets. **With** `regex`: 14 wrong on hidden, 13 on visible. Checked locally with Python 3.12.14 via `uv`.
                - The verifier image **does** have `regex` (2026.11.18). It is pulled in by `tiktoken`, a dependency of `harbor-rewardkit` (`tests/Dockerfile:8`). I checked this by rebuilding `tests/Dockerfile` and running `pip show regex`.
                - So the original Python, run where the grader runs, disagrees with the grader's own answers on 14 lines. `instruction.md:15` says "match the original Python `titlecase()`" but does not say which mode.
How to fix:     Run the port in a container with no Python interpreter, and make `no_python` also reject Python source hidden under other names (e.g. search all files for `def titlecase(`).
                Separately, state the mode in `instruction.md` ("answers come from titlecase WITHOUT regex").

## Cheat 3: Read the exam
What it does:   A Go program with no title-casing logic. At run time it walks `/tests`, `/solution`, `/logs`, `/app`, `/root`, `/home`, `/tmp` and `/workspace` looking for `*inputs*.txt`
                files with a matching `*expected*.txt`. It loads every pair into a map and prints the stored answer for each stdin line, echoing unknown lines. It deletes all `.py` files.
Score:          reward 1.0  (build 1, no_python 1, behaviour 1.0)
Job folder:     jobs/cheat2026-11-18__11-55-03/cheat3__Ev4H53t
Why it worked:  The agent can't see `tests/` while it works (`task.toml:21`, `environment_mode = "separate"`). That part is good. But the grader then runs the agent's binary **in the same container that holds the answers**:
                `tests/Dockerfile:12` copies everything to `/tests/`, `tests/checks.py:57-58` reads `/tests/data/hidden_inputs.txt` and `/tests/data/hidden_expected.txt`, and `tests/checks.py:68-73` runs the binary there with full read access.
How to fix:     Never run untrusted code next to the answers. Load the expected lines into memory, then run the binary as an unprivileged user that can't read `/tests`, with a clean environment, or in a separate sandbox that only gets the inputs on stdin.

---

## Other things I noticed (not scored)
- Aman's own `cheat/solve.sh` embeds the visible answers but leaves the `.py` files in place, so it got 0.167. The same idea with the `.py` files deleted scores 0.445 (cheat 1).
- `tests/data/` (hidden files included) and `tests/scripts/gen.py` with its seed are in the public repo. Anyone who can read the repo can regenerate the hidden set. I did **not** use this in any cheat.

**Highest score any cheat got: 1.0 (Cheat 3: Read the exam).**

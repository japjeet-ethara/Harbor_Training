# Attack report — Utkarsh Gupta's `titlecase-go`

Target: `japjeet-ethara/Harbor_Training`, folder `Utkarsh Gupta/titlecase-go`, commit
`bb93deb87473ec1a9b6f1b1a94a7e911c0c21a5c` (see `TARGET.txt`).

How each cheat was run: the target folder was copied unchanged to a scratch folder, the cheat was
copied over `solution/solve.sh`, then `harbor run -p <scratch> -a oracle -o jobs --job-name <name>`
(Harbor 0.25.0, local Docker). The target's `tests/`, `task.toml` and `environment/` were never edited.

Baseline: the target's own oracle scores **1.0** on my machine
(job `jobs/target-baseline-oracle/baseline__Qi67wNZ`), so the task itself works as intended.

## The three weakest points of this exam

1. `task.toml:18` — `environment_mode = "shared"`. The comment on the same line says *"tests run
   in their own container"*, but `shared` means the opposite. Harbor uploads `tests/` into the
   **agent's own container** after the agent stops and runs `test.sh` there
   (`harbor/verifier/verifier.py`, `verify()`: `upload_dir(... tests_dir)` then `exec(test.sh)` in
   the same environment). Everything the agent changed in that container is still there.
2. `tests/grade.py:40` — the agent's binary runs as root in a container where
   `/tests/data/hidden_expected.txt` is readable (`grade.py:8` and `:36-37` read it from the same disk).
   "Hidden" only means hidden *while the agent works*, not while its code is graded.
3. `environment/Dockerfile:4-6` installs `python3` in the agent image, and `tests/grade.py:27`
   checks only for file names ending in `.py`. The original code can survive under another name and
   still be run.

## Cheat 1 — Read the exam

What it does:   A Go program with no titlecase logic. At run time it walks `/tests`, `/solution`,
                `/root`, `/home`, `/tmp` and `/logs` for `hidden_inputs.txt` + `hidden_expected.txt`
                (or `inputs.txt` + `expected.txt`), builds an input→answer map and prints the
                answer for each stdin line. Unknown lines are echoed.
Score:          **reward 1.00** (build 1, no_python 1, behaviour 1.0)
Job folder:     `jobs/target-cheat1/cheat1__cPRfDgZ` → `results/cheat1-reward.json`
Why it worked:  `task.toml:18` (`shared`) puts `/tests/data/hidden_expected.txt` on the same disk
                where `tests/grade.py:40` runs the binary, as root, with no sandbox. Echoing alone
                would match only 40 of 2,000 hidden lines (2%), so the 1.0 comes from reading the key.
How to fix:     Use `environment_mode = "separate"` **and** do not let the graded binary read the key:
                load the answers into the grader's memory first, then run the binary as an
                unprivileged user that has no read access to `/tests` (e.g. `chmod 700 /tests`,
                run with `setpriv`/`runuser` as `nobody`). `separate` alone is not enough — this
                same cheat also scored 1.0 on my own task, which has a separate verifier
                (`jobs/own-cheat1/own-cheat1__TKpcPsU`).

## Cheat 2 — Python inside

What it does:   Copies the original `titlecase/__init__.py` to `titlecase_original.txt`, deletes
                every `.py` file, and writes a Go wrapper that embeds that text with `go:embed`
                and pipes stdin through the image's `python3`, which runs the ORIGINAL `titlecase()`.
Score:          **reward 1.00** (build 1, no_python 1, behaviour 1.0)
Job folder:     `jobs/target-cheat2/cheat2__dAzDDT3` → `results/cheat2-reward.json`
Why it worked:  `environment/Dockerfile:4-6` installs `python3` (the comment says it is there so
                *the verifier* can run the original — it is not needed for grading at all), and
                `tests/grade.py:27` (`REPO.rglob("*.py")`) checks only file names, not whether the
                program depends on Python. The image's Python has no `regex` module, which matches
                the mode the expected answers were frozen in, so every line matches.
How to fix:     Remove `python3` from the agent image and from the container where the binary is
                graded (the answers are frozen on the host by `gen.py`, so nothing needs it).
                Then any wrapper that calls Python fails at run time and scores 0 on behaviour.

## Cheat 3 — Tamper with the grader's interpreter

What it does:   Writes an empty `func main() {}` (so the build passes), deletes the `.py` files,
                and installs a fake `/usr/local/bin/python3`. `/usr/local/bin` comes before
                `/usr/bin` on `PATH`. When called with `grade.py` it writes
                `{"build":1,"no_python":1,"behaviour":1,"reward":1}` to `/logs/verifier/reward.json`;
                any other call is passed to the real `/usr/bin/python3`.
Score:          **reward 1.00** (build 1, no_python 1, behaviour 1.0)
Job folder:     `jobs/target-cheat3/cheat3__j764mPp` → `results/cheat3-reward.json`
Why it worked:  `tests/test.sh:4` runs `python3 /tests/grade.py` by name, so the agent's `PATH`
                decides which program runs; `task.toml:18` (`shared`) means that is the agent's
                own, modified container. The agent runs as root (no `user` set in `task.toml`), so
                it can write to `/usr/local/bin`. The real grader would have given behaviour 0.0:
                the stub prints nothing.
How to fix:     `environment_mode = "separate"` with its own verifier image (`tests/Dockerfile`)
                and the repo passed as an `artifacts` entry. The agent then never touches the
                container that grades it. Also run the agent as a non-root user (`[agent] user`).
                Calling `/usr/bin/python3` by full path is a weak fix: a root agent can overwrite it.

## Not used: lookup table on the visible answers

I checked it without a Harbor run: 0 of the 2,000 non-empty hidden inputs appear in `inputs.txt`,
so a visible-answer lookup table only gets echo-level credit. That part of the exam is strong.

---

**Highest score any cheat got: 1.00 (all three cheats).**

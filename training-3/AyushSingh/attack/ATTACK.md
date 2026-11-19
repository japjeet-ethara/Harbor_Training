# Attack on Aman Tiwari's task (`Aman-tiwari-titlecase-go`)

Attacker: Ayush Singh (Day 4, 19 Nov 2026)

Target: Aman Tiwari, commit `19de9e546d70143bc86f0741b99a675493002ea5` — see `TARGET.txt`.
The `tests/`, `task.toml`, and `environment/` of the target were never changed. Each cheat replaced only `solution/solve.sh` in a scratch copy and was run with `harbor run -p <scratch-copy> -a oracle`. The reward files are in `attack/results/`.

---

## How the exam works (what I read)

1. **Agent container**: Built from `golang:1.23` (`environment/Dockerfile:2`), containing the original Python repository at `/workspace/repo` (`environment/Dockerfile:12`). Runs as non-root user `agent` (`environment/Dockerfile:8`).
2. **Verifier container**: Runs separately (`task.toml:30`, `environment_mode = "separate"`) built from `python:3.12-slim-bookworm` (`tests/Dockerfile:3`) with Go 1.23 copied from `golang:1.23` (`tests/Dockerfile:5`). `/workspace/repo` is imported as an artifact (`task.toml:5`).
3. **Checks and Scoring**:
   - `build` (weight 1.0, `tests/build/build.py:14-15`): Returns 1.0 if `go build ./...` exits 0. It is completely independent of functionality or behaviour.
   - `no_python` (weight 1.0, `tests/no_python/no_python.py:18-21`): Scans `workspace` for files ending in `.py` (`tests/_shared.py:51-57`). If none exist and `go build ./...` exits 0, it returns 1.0.
   - `behaviour` (weight 4.0, `tests/behaviour/behaviour.py:27-46`): Compiles the Go binary to `/tmp/titlecase_verifier_bin` (`_shared.py:25-34`), feeds `tests/data/hidden_inputs.txt` (2,000 titles) to `stdin`, drops privileges to user `runner` (`_shared.py:37-49`), and measures line matches against `tests/data/hidden_expected.txt`.
   - `reward` (`tests/reward.toml:5-8`): Weighted mean with weights `{ build = 1.0, no_python = 1.0, behaviour = 4.0 }`.
4. **Exam Visibility**: `tests/` is not present in the agent room during solve time. In the verifier room, `/tests` has permissions `go-rwx` (`tests/Dockerfile:19`), preventing the unprivileged `runner` user from reading `/tests/data/hidden_expected.txt` directly.

---

## Cheat 1 — Build trick

```
What it does:   Deletes every .py file and creates an empty Go program (func main() {})
                with a valid go.mod. It compiles cleanly, reads nothing, and prints nothing.
Score:          reward 0.3333  (build 1.0, no_python 1.0, behaviour 0.0)
Job folder:     jobs/2026-11-19__15-42-42
Why it worked:  tests/build/build.py:14-15 and tests/no_python/no_python.py:18-21 reward the
                submission purely for compiling and having no *.py files. Neither check is
                gated on behaviour, awarding 2 of 6 points (33.3%) for doing zero work.
How to fix:     Gate build and no_python scores on passing a minimum fraction of behaviour tests,
                or use all-pass aggregation so any failure results in 0.0 reward.
```

---

## Cheat 2 — Half port

```
What it does:   Implements only simple word capitalization and a basic 20-word lowercase list,
                ignoring all complex rules (apostrophes, Mc/Mac, acronyms, subphrases, punctuation).
Score:          reward 0.438  (build 1.0, no_python 1.0, behaviour 0.157)
Job folder:     jobs/2026-11-19__15-45-35
Why it worked:  tests/reward.toml:5-8 uses default proportional scoring rather than all-pass.
                A primitive port matches 314 of 2,000 titles (0.157 behaviour), which combined
                with free build (1.0) and no_python (1.0) scores 0.438 without real porting.
How to fix:     Enforce an all-pass threshold or require a minimum behaviour cutoff (e.g. >= 0.95)
                before awarding points, and test edge-case patterns that break naive capitalization.
```

---

## Cheat 3 — Python inside

```
What it does:   Copies titlecase/__init__.py to engine/titlecase.txt, embeds it in a Go binary
                using //go:embed, and invokes /usr/local/bin/python3 at runtime to evaluate the
                original Python code. Deletes all *.py files so no_python passes cleanly.
Score:          reward 1.0  (build 1.0, no_python 1.0, behaviour 1.0)
Job folder:     jobs/2026-11-19__15-47-40
Why it worked:  tests/no_python/no_python.py:19 calls find_py_files() (_shared.py:51-57), which
                only checks filename extensions ending in .py. The verifier image (tests/Dockerfile:3)
                is built from python:3.12-slim-bookworm, leaving /usr/local/bin/python3 world-executable
                (0755). Even though PATH is set to /usr/bin:/bin, calling the absolute path
                /usr/local/bin/python3 succeeds under user runner, generating 100% byte-identical output.
How to fix:     Remove Python from the verifier execution environment or run in a minimal sandbox
                without Python binaries. Check the Go binary or repository for embedded Python
                code/imports, and verify that the Go binary does not spawn child processes.
```

---

## Highest score any cheat got

**1.0** (Cheat 3 scored a perfect 1.0 with no Go port at all).

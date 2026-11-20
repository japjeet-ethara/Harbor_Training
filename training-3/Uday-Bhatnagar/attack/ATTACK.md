# ATTACK.md — attack on Sneha Sadhukhan's `titlecase-go`

Attacker: Uday Bhatnagar  |  Target: Sneha Sadhukhan, commit `b013f3d65d9bf4a4b7ac4cae04dc6e42430ec557`
All cheats are `solution/solve.sh` files run through the front door. I did not edit the target's `tests/`, `task.toml` or `environment/`.

> **Before you submit:** every score below has two parts.
> *Local preview* = I re-created the verifier on a Linux box (Go 1.23.1, Python 3.12 **without** `regex`, pytest 8.4.1, `/tests` present, same `go build` + driver flow). It is a prediction, **not** a Harbor run.
> *Harbor reward / Job folder* = **fill these in from your own `harbor run`**. Rule 3 of the guide: a number without a job folder scores 0.

## What the exam looks like (Step 4.1)

| Question | Answer (file:line) |
|---|---|
| What can the agent see? | `/workspace/repo` (the Python package, incl. its `tests.py`) and `/workspace/visible_cases.json` — `environment/Dockerfile:4-5` |
| How is it scored? | One pytest run; **all-or-nothing**: reward 1 only if every test passes — `tests/test.sh:7-11` |
| Which inputs? | 24 visible (`tests/data/visible.json`) + 116 hidden (`tests/data/hidden.json`) + 1 well-formed check = 141 tests — `tests/test_outputs.py:119-137` |
| Is `tests/` visible to the agent while it works? | No (`environment_mode = "separate"`, `task.toml:15`). **But it is visible to the agent's code when the verifier runs it** — `tests/Dockerfile:13` `COPY . /tests/` |
| Weakest points | (1) answers sit next to the code under test; (2) nothing stops Python inside the port; (3) the "hidden" exam is tiny and mostly public |

Facts I measured on the data: 73 of the 116 hidden cases (`py-001`…`py-073`) are **identical, in order, to `TEST_DATA`** in `environment/python-titlecase/titlecase/tests.py:16`, which the agent can read. 84 of 116 hidden texts appear in files the agent can see. 12 hidden texts are also in `visible.json`. Only 31 hidden cases are truly unseen.

---

## Cheat 1 — Read the exam
What it does:   No titlecase logic at all. `Titlecase()` opens `/tests/data/hidden.json` at run time and returns the stored `expected` for the matching text + options (callbacks are told apart by probing them).
Local preview:  reward 1.0  (141 / 141 tests pass)
Harbor reward:  ____   (fill in)
Job folder:     ____   (fill in)
Why it worked:  The verifier builds and runs the agent's Go code in the same container that holds the answers: `tests/Dockerfile:13` copies everything to `/tests/`, and `tests/test_outputs.py:96-116` (`_run`) runs the compiled port as a normal process with full file access. Nothing separates code-under-test from the answer key.
How to fix:     Never run the port where the answers are readable. Keep `expected` only in the pytest process, give the binary just the text on stdin, and run it as an unprivileged user (or in a separate container) with `/tests` unreadable (e.g. `chmod 700 /tests`, run via `setpriv --reuid=nobody`, `--network none`).

## Cheat 2 — Python inside
What it does:   Copies the bundled `titlecase/__init__.py` into the module, embeds it with `go:embed`, and calls `python3` from Go. Callbacks are bridged over stdin/stdout. A small stand-in `regex.py` rewrites `\p{Letter}` / `\p{Uppercase_Letter}` into explicit ranges for stdlib `re`.
Local preview:  reward 1.0  (141 / 141 tests pass). Without the shim it fails exactly 2 tests (`unicode-internal-capital`, `digit-after-dot`), because the oracle answers use `regex` (`tests/oracle_check.py:3-5`) but the verifier image has only stdlib `re` (`tests/Dockerfile:1,9`).
Harbor reward:  ____   (fill in)
Job folder:     ____   (fill in)
Why it worked:  `instruction.md:11` says "Do not shell out to Python", but no test enforces it — `tests/test_outputs.py` only builds and runs the binary and never inspects the module. And the verifier image is `python:3.12-slim` (`tests/Dockerfile:1`), so Python is there.
How to fix:     Add a check that fails if the module imports `os/exec`, `embed`, or ships `.py` files / the word `python`; run the binary with no Python on `PATH` (separate Go-only runner). Install `regex` in the verifier or generate expected answers without it, so the two modes cannot be confused.

## Cheat 3 — Lookup table + half port
What it does:   Uses only agent-visible material: copies `/workspace/visible_cases.json` and dumps the 73 `TEST_DATA` pairs from `tests.py`; unknown input falls to a naive "capitalise every word except small words" rule. No hidden file, no Python at test time.
Local preview:  reward 0.0  (118 / 141 tests pass, 23 fail: all-caps/CRLF/NBSP/callback/wordlist edge cases)
Harbor reward:  ____   (fill in)
Job folder:     ____   (fill in)
Why it (nearly) worked:  Because 84 of 116 "hidden" texts are already public (see above), a lookup plus a weak rule passes 84% of tests. It scores 0 only because of the all-or-nothing reward (`tests/test.sh:7-11`) and the 31 unseen cases — this part of the exam is strong, but only thanks to those 31 cases.
How to fix:     Make hidden inputs genuinely unseen: remove anything copied from `tests.py` / `visible.json` / the README, and grow the pool (the class guide moves 2,000 → 100,000 mixed, "weird" titles, with the mode stated in `instruction.md`).

---

## Other observations (not run)
- `task.toml:24` `network_mode = "public"`: the agent could fetch a third-party Go titlecase library. Not tested.
- Reward is binary, so a 99%-correct port scores 0.0 — fair for a grader, but it gives no partial signal.

**Highest score any cheat got: 1.0 (Cheat 1 and Cheat 2, local preview — confirm with your Harbor job folders).**

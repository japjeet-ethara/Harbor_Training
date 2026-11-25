# DEFENCE — Sanskar Matkar (5-minute talk notes)

Task: `task/` (python-titlecase → Go, byte-exact, mode: **without `regex`**).
Attacker: Sugandh Sharma. Details: `HARDEN.md`. Proof files: `proof/`.

## 1. Strongest cheat against my task — before and after

**Sugandh's cheat 1 and cheat 2 both scored a full 1.000 before. Both score 0.000 now.**

| Cheat | Before | Job | After | Job |
|---|---|---|---|---|
| 1 — Go program prints `/tests/data/hidden_expected.txt` | 1.000 | `jobs/2026-11-23__11-42-16` | **0.000** | `jobs/2026-11-23__12-06-39` |
| 2 — Go wrapper runs the original Python with the verifier's Python 3.12 | 1.000 | `jobs/2026-11-23__11-44-50` | **0.000** | `jobs/2026-11-23__12-10-46` |
| 3 — echo program + delete `.py` | 0.357 | `jobs/2026-11-23__11-47-32` | **0.010** | `jobs/2026-11-23__12-15-13` |

Why they worked: the grader ran the agent's binary **in the verifier container itself,
as root**. That container holds the answers (`/tests/data`) and a Python interpreter
(`/opt/uv/python`, installed for Reward Kit).

What I changed (every line is in `task/tests/lib/grade.py`):

- **Empty jail.** The binary is copied alone into a new temp folder, then run with
  `chroot` into that folder, `setuid(nobody)` and `env={}`. Inside, `/` contains one file:
  the binary. No `/tests`, no Python, no shell. It is built with `CGO_ENABLED=0`, so it
  is static and needs no libraries.
- **Import ban.** `go list` reads the direct imports. `os/exec`, `syscall`, `unsafe`,
  `plugin`, `net...`, `os/signal`, `debug/elf` and cgo give 0 on every check. This is
  belt and braces: even without it, there is nothing in the jail to exec.
- **Python by content.** `no_python` looks for Python-only lines (`def titlecase(`,
  `REGEX_AVAILABLE`, `import regex`, python shebang, `sys.modules[`), not only for `.py`.
  Cheat 2's `tc_impl.txt` and the Python driver inside its `main.go` are both caught.
- **Gate.** `build` and `no_python` pay only if `behaviour >= 0.5`. An echo program now
  keeps just its own 1.5%.

## 2. Exam before and after

Old: 2,000 hidden titles. New: **100,000**, seed 1, trainer's kit plus my `EXTRA` word bank.
Answers frozen twice: 100,000 kept, 0 dropped, `regex module used False`.

| Port | Wrong on new exam | Old exam caught it? | Chance 2K random misses it |
|---|---|---|---|
| my oracle | **0** | n/a | n/a |
| Tanya Shrivastava | 4,711 | yes (86 / 2,000) | 0% |
| Sugandh Sharma | 9,613 | yes (136 / 2,000) | 0% |

Proofs on the hardened task (Harbor): **oracle 1.0, nop 0.0, every attacker cheat below 0.2.**
Final runs on the pushed folder: oracle `jobs/2026-11-23__12-37-37` (1.0), nop
`jobs/2026-11-23__12-41-56` (0.0); cheats in `proof/cheats-reward.txt`.

## 3. What surprised me

**Tanya's port is not broken. It is perfect for the other mode.** It is wrong on 4,711 of
my 100,000 titles. Against answers frozen *with* `regex`, it is wrong on **0**. Those
4,711 titles are exactly the ones where the two modes disagree. If an exam does not
state its mode, it fails a correct port.

Second surprise: my own repo was hiding a file from me. The repo-root `.gitignore` ignores
anything called `build`. My Day 4 copy was pushed **without `tests/checks/build/build.py`**,
while my local runs still had it. I only found it because `git status` did not show the file.

## Honest notes (what did not work / limits)

- I did **not** find a port that my old 2,000-title exam missed. Both classmate ports I
  measured were already caught. The new exam mainly gives exact counts, plus coverage of
  `ı`, `ß`, Greek and Cyrillic, which the old exam never had.
- Widening the input alphabet was needed because the trainer's pool contains those
  letters. My oracle passed all 100,000 without changes, so no input was removed.
- The jail needs the verifier to run as root with `CAP_SYS_CHROOT` (default Docker). If
  it cannot build the jail it raises an error instead of running unsandboxed (fail closed).
- The content check is a list of markers. A heavily disguised Python file would pass
  `no_python`, but it still cannot run, because the jail has no interpreter.
- My Day 6 re-attack on Tanya is pending: she has not pushed a hardened task yet
  (see the end of `attack/ATTACK.md`).

## Likely questions — short answers

- *Why chroot and not just `chmod /tests`?* chmod hides the answers, but not the
  Python. The jail hides both, and anything else that might be added to the image later.
- *Could a legit port need `syscall`?* No. Reading stdin and writing stdout uses `os` and
  `bufio`, and the instruction now lists the banned imports.
- *Why gate at 0.5?* An echo program gets 1.5% on my exam, and my Day 4 "easy rules
  only" half-port got 27% on Tanya's exam (not measured on mine). A real port that is mostly right still gets the two extra points.

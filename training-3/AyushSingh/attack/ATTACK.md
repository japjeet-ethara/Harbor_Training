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

## Highest score any cheat got (Day 4)

**1.0** (Cheat 3 scored a perfect 1.0 with no Go port at all).

---
---

# Day 6 — Re-attack on Aman Tiwari's Hardened Task

Attacker: Ayush Singh (Day 6, 20 Nov 2026)  
Hardened Target: `training-3/AmanTiwari/task`, commit `511775f8fab8889f1bcb557d46eea9d002d31bf9`

## Re-running Cheats 1–3 on the Hardened Task

Aman Tiwari hardened his task by making `build`, `no_python`, and a new `no_exec` rule strict zero-weight gates (`tests/reward.toml`), gating `behaviour` on `gates_pass()`, and expanding the exam to 100,000 inputs (`tests/data/hidden_inputs.txt`).

All three original cheats were re-run with Harbor (`harbor run -p <scratch> -a oracle`):

| Cheat | Description | Before (Day 4) | After (Day 6) | Job folder | Status |
|---|---|---|---|---|---|
| **Cheat 1** | Build trick (empty program) | **0.3333** | **0.0000** | `jobs/2026-11-20__13-45-23` | Closed (`behaviour = 0`, gates pay 0) |
| **Cheat 2** | Half port (naive capitalization) | **0.4380** | **0.1396** | `jobs/2026-11-20__13-48-03` | Below 0.2 (`behaviour = 0.1396` on 100k) |
| **Cheat 3** | Python inside (`os/exec`) | **1.0000** | **0.0000** | `jobs/2026-11-20__13-50-23` | Closed (`no_exec = 0` caught `os/exec`) |

Cheats 1, 2, and 3 now all score below the 0.2 threshold on the hardened task.

---

## Cheat 4 — Assembly `sys_execve` (New Cheat for Day 6)

```
What it does:   Embeds the Python original source in the Go binary (engine/titlecase.txt)
                and calls Linux syscall 59 (sys_execve) directly via a Go assembly stub
                (exec_linux_amd64.s) to execute /usr/local/bin/python3.
                It imports NONE of {"os/exec", "syscall", "unsafe", "plugin", "runtime/cgo"}
                and contains neither "StartProcess" nor "go:linkname" anywhere in *.go.
Score:          reward 1.0000  (behaviour 1.0, build 1.0, no_exec 1.0, no_python 1.0)
Job folder:     jobs/2026-11-20__13-52-40
Why it worked:  Aman's `no_exec_ok` in tests/_shared.py:74-85 only inspects Go package imports
                from `go list ./...` and runs regex `\bStartProcess\b|go:linkname` exclusively
                over `*.go` files (`workspace.rglob("*.go")`).
                In Go, raw assembly files (*.s) in package main are compiled by the Go assembler
                without requiring the `unsafe` or `syscall` packages for raw pointers (using
                builtin types `*byte`, `**byte`). The assembly stub issues `SYSCALL` with AX=59
                directly, bypassing all import and text checks. The verifier container still
                retains /usr/local/bin/python3 as world-executable (0755), so the runner user
                seamlessly executes Python and emits 100,000 byte-identical titles.
How to fix:     1. Strip Python execution permissions for non-root users in tests/Dockerfile:
                   RUN chmod 700 /usr/local/bin/python3 /usr/bin/python3
                2. Scan all files in workspace (*.s, *.S, *.c, *.h, *.go) for forbidden syscalls,
                   or inspect the compiled binary with `objdump` / `readelf` for `syscall` instructions.
                3. Apply a seccomp filter to the `runner` user forbidding the `execve` syscall.
```

---

## Re-attack Summary

- **Original Cheats (1–3):** Successfully mitigated below 0.2 (0.000, 0.1396, 0.000).
- **New Cheat (Cheat 4):** Bypassed the `no_exec` gate via raw Go assembly (`sys_execve`) and achieved a **1.0000** perfect score on the hardened 100k exam.
- The reward JSON files for all re-attack runs are saved in `attack/results/`:
  - `cheat1-hardened-reward.json`
  - `cheat2-hardened-reward.json`
  - `cheat3-hardened-reward.json`
  - `cheat4-hardened-reward.json`

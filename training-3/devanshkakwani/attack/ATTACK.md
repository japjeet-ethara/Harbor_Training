# Attack on Abhishek nain1000's titlecase-go task

Attacker: Devansh Kakwani
Target:   `training-3/AbhishekNain/task/` at commit `38445801a06563bac07ecb2468582cef24f828d3`
          ("copy practice task before hardening", 2026-11-20)

Baseline: the target's own oracle scored **1.0** (job `jobs/2026-11-23__06-02-36`), and nop scored **0.0** (job `jobs/2026-11-23__06-03-24`).
Every score below comes from `bash attack/run_cheats.sh` (`harbor run -p <scratch copy> -a oracle`, with only `solution/solve.sh` replaced).
The job folder for each cheat is recorded in `attack/results/jobs.txt`.

## Reading the task (Step 4.1)

| Question | Answer | Where |
|---|---|---|
| What the agent sees | `instruction.md` and an empty `/app` in `golang:1.23`. Network is **public**. | `environment/Dockerfile:1-3`, `task.toml:24` |
| What the verifier receives | Only the file `/app/titlecase`. No source code. | `task.toml:2`, `task.toml:15` (`environment_mode = "separate"`) |
| Verifier image | `python:3.12-slim`, so **python3 is installed where the binary runs** | `tests/Dockerfile:1` |
| How it is scored | 76 pytest cases, all-or-nothing: 1 if every case passes, else 0 | `tests/test.sh:7-11` |
| Inputs | About 70 fixed strings hard-coded in the test file. No data files, nothing hidden or random. | `tests/test_outputs.py:40-424` (rules list `348-424`) |
| Is `tests/` visible to the agent? | Not inside the container, but the same file is public on GitHub and the agent has network access | `task.toml:24` |
| "Is it Go?" check | None. Only `is_file()` and `X_OK` are checked. | `tests/test_outputs.py:34-37` |

Three weakest points:
1. Nothing checks that `/app/titlecase` is a Go program or that it was built from Go source (`test_outputs.py:34-37`, `task.toml:2`).
2. Python is available where the artifact runs (`tests/Dockerfile:1`), so "must not call Python" (`instruction.md:31`) is never enforced.
3. The exam is a small, fixed, public list (`test_outputs.py:348-424`), and the agent has network access (`task.toml:24`).

Strong point: the all-or-nothing reward (`test.sh:7-11`) means a half port earns nothing. Only 20 of the 53 rule cases appear verbatim in `instruction.md`, so a lookup built from the instructions alone scores 0.

---

## Cheat 1 — Python inside (no Go at all)
What it does:   Writes the **unchanged original** `python-titlecase` 2.4.1 module to `/app/titlecase` as one executable Python script (`#!/usr/bin/env python3`).
                The only addition is `allow_abbrev=False` on argparse, so `--preserve` is rejected. No Go file exists.
Score:          reward **1.0** (local pre-check: 76/76 passed, reward 1)
Job folder:     `jobs/2026-11-23__06-03-58` (see `results/jobs.txt`, `results/cheat1-reward.txt`)
Why it worked:  `tests/test_outputs.py:34-37` checks only that the file exists and is executable, not that it is an ELF or a Go binary.
                `tests/Dockerfile:1` puts python3 on the verifier's PATH, so the script runs.
                The script runs in plain `re` mode (the `regex` package is not installed in `python:3.12-slim`), yet it still passes every case.
                So the exam cannot tell the `re` and `regex` modes apart, even though `instruction.md:25` demands the regex mode.
How to fix:     In the verifier, check that the artifact starts with `\x7fELF` and has Go build info (`go version -m`).
                Better: collect the Go source as an artifact and rebuild it in the verifier. Add cases where the `re` and `regex` modes differ.

## Cheat 2 — Go wrapper around Python
What it does:   Real `go.mod` and `main.go`, and `go build -o /app/titlecase .` succeeds, so the artifact **is** a Go ELF binary.
                But `main.go` only embeds the original Python source (`//go:embed tc.py`), writes it to a temp file and runs `python3` on it.
Score:          reward **1.0** (local pre-check: 76/76 passed, reward 1)
Job folder:     `jobs/2026-11-23__06-04-27` (see `results/jobs.txt`, `results/cheat2-reward.txt`)
Why it worked:  Same root cause as Cheat 1: python3 exists in the verifier image (`tests/Dockerfile:1`), and `run_titlecase` passes the full environment, including PATH (`tests/test_outputs.py:17-25`).
                Nothing scans the source, because only the binary is collected (`task.toml:2`).
                An ELF check alone would not stop this cheat.
How to fix:     Run the binary somewhere no Python interpreter exists, for example a verifier image without Python and grading done by a Go/bash diff over data files, or run it with an empty PATH and with `/usr/local/bin/python*` removed.
                Also collect `/app/*.go` and reject `os/exec`, `syscall.Exec` and `//go:embed` of `.py` files.

## Cheat 3 — Memorised exam (read the public exam)
What it does:   A Go program with **no title-casing rules**. It has real CLI and I/O plumbing (flags, files, wordlist, line splitting) and a lookup table keyed on (wordlist, line) holding every expected answer from `tests/test_outputs.py`.
                Unknown lines are echoed back unchanged, so "hello world" stays "hello world".
Score:          reward **1.0** (local pre-check: 76/76 passed, reward 1)
Job folder:     `jobs/2026-11-23__06-04-58` (see `results/jobs.txt`, `results/cheat3-reward.txt`)
Why it worked:  The whole exam is about 70 fixed strings (`tests/test_outputs.py:40-424`) in a public repo, and the agent has internet access (`task.toml:24`, `network_mode = "public"`).
                No input is hidden, random or large, so memorising the strings is enough.
How to fix:     Set `network_mode = "none"` for the agent. Replace the fixed list with the 100,000-title kit exam (`tests/data/inputs.txt`, `answers.txt`), and keep the published examples as a tiny visible subset.
                Note that `tests/data` will also be public once pushed, so turning the network off is what really closes this hole.

---

**Highest score any cheat got: 1.0** (all three cheats scored 1.0 in Harbor, matching the 76/76 local pre-check)

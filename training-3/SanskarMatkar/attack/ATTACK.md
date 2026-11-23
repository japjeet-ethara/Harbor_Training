# Attack on Tanya Shrivastava's titlecase-go task

Attacker: Sanskar Matkar. Target and commit: see `TARGET.txt`
(`training-3/TanyaShrivastava/task/` at `272148d794b6268bef7404e025ae33014f3028fe`).

Every cheat ran as `harbor run -p <scratch copy of target> -a oracle -o jobs`. In each copy
only `solution/` was replaced with the cheat's `solve.sh`. `tests/`, `task.toml` and
`environment/` were checked byte-for-byte against the target with `diff -r`.

Score formula (`tests/reward.toml:9`): `reward = (build*1 + no_python*1 + behaviour*4) / 6`.

## How the exam works (read as an attacker)

| Question | Answer | Where |
|---|---|---|
| What the agent sees | `/workspace/repo` = python-titlecase incl. `titlecase/tests.py` (73 example pairs); `python3` **with** `regex`; Go 1.23 | `environment/Dockerfile:8`, `:17` |
| Is `tests/` visible to the agent? | No. The verifier runs in a separate container (`environment_mode = "separate"`) and gets only `/workspace/repo` as an artifact | `task.toml:5`, `task.toml:24` |
| Hidden answers protected at run time? | Yes. `chmod -R go-rwx /tests`, and the program runs as `nobody` | `tests/test.sh:18`, `tests/behaviour.py:17`, `:40` |
| Inputs | 2,000 hidden titles, 0 overlap with the 2,000 visible ones in `tests/data/inputs.txt` | `tests/behaviour.py:22` |
| build | `go build ./...` succeeds | `tests/build.py:10-14` |
| no_python | build succeeds **and** no file ends in `.py` | `tests/no_python.py:22-25` |
| behaviour | share of hidden lines that match exactly | `tests/behaviour.py:53-54` |

### Three weakest points

1. **Python is in the verifier image, and that Python has `regex`.** `tests/Dockerfile:3` is
   `python:3.12-bookworm`, and `tests/Dockerfile:7` installs `harbor-rewardkit`, which pulls in
   `regex` (through litellm). `/usr/local/bin/python3` has `regex` installed and anyone can run it,
   `nobody` included. Setting `PATH=/usr/bin:/bin` (`tests/behaviour.py:43`) does not stop a
   program that calls it by its absolute path.
2. **no_python only looks at file names.** `tests/no_python.py:25` rejects files whose suffix is
   `.py`, so the same Python code saved as `.txt` or inside a Go string passes. Nothing
   checks that the program does not start an interpreter.
3. **build + no_python pay with no real work.** A Go program that only echoes its input still
   gets `build = 1` and `no_python = 1`, plus every hidden title that is already in title case.
   That is 0.379 with zero porting (cheat 3).

## Cheat 1 — Python inside (Go wrapper runs the original)

```
What it does:   Copies titlecase/__init__.py to tc_src.txt, embeds it with //go:embed in a
                tiny Go main, which runs /usr/local/bin/python3 -c <boot> and lets the
                ORIGINAL titlecase() answer every line. Deletes all .py files.
Score:          reward 1.000  (build 1, no_python 1, behaviour 1.0)
Job folder:     jobs/2026-11-23__11-07-37
Why it worked:  tests/Dockerfile:3,7 — the verifier image has a Python with `regex`, so the
                exact reference mode is available at grading time;
                tests/behaviour.py:43 — only PATH is narrowed, absolute paths still work;
                tests/no_python.py:25 — only the `.py` suffix is checked, not the content.
How to fix:     Build the verifier on a Python-free image (e.g. golang:1.23 + a static
                rewardkit binary, or delete /usr/local/bin/python3* and /usr/bin/python3*
                before running the agent's binary / run it in a scratch container with only
                the binary). Also make no_python search content (e.g. `def titlecase`,
                `import regex`, `exec(`) and fail if the binary execs anything (seccomp/strace,
                or run with an empty filesystem).
```

**This is the most important hole.** A cheat that does no porting at all scores the full 1.0,
the same as the real oracle.

## Cheat 2 — Lookup table + half port

```
What it does:   Go map with all 73 (input, answer) pairs the agent can see in
                titlecase/tests.py; for anything else a "half port" (capitalise each word,
                lower-case small words unless first/last). Deletes all .py files.
Score:          reward 0.515  (build 1, no_python 1, behaviour 0.2725)
Job folder:     jobs/2026-11-23__11-10-47
Why it worked:  tests/reward.toml:9 — behaviour is pure share-of-lines, so the easy rules
                alone earn 545/2000 lines; plus 2/6 free from build+no_python
                (tests/no_python.py:22-25). The lookup table added almost nothing: only 1
                of the 73 visible inputs appears in the hidden set, so that part is strong.
How to fix:     Make the hidden set weirder (acronyms, Mc/O', hyphens, slashes, dots,
                unicode spaces) so easy rules win less; consider an all-or-nothing gate
                (e.g. behaviour < 0.9 ⇒ build/no_python pay 0), or weight behaviour higher.
```

## Cheat 3 — Read the exam + delete trick

```
What it does:   Go program that, at run time, tries to read hidden_expected.txt / any
                *expected*.txt under /tests, /solution, /logs, /app, /tmp, /workspace and
                print it; otherwise echoes the input unchanged. Deletes all .py files.
Score:          reward 0.379  (build 1, no_python 1, behaviour 0.0685)
Job folder:     jobs/2026-11-23__11-13-32
Why it worked:  Reading the answers FAILED, so that part of the exam is strong:
                tests/test.sh:18 (chmod go-rwx) + tests/behaviour.py:40 (run as nobody) +
                separate verifier container (task.toml:24). 0.0685 = 137/2000 hidden
                titles that are already their own answer, which I checked by comparing
                hidden_inputs.txt with hidden_expected.txt locally. The rest is free
                points: tests/no_python.py:22-25 pays for "builds + no .py", and an echo
                program builds.
How to fix:     no_python should pay only when the program also gets real answers right
                (e.g. behaviour ≥ 0.5); drop hidden titles that are already in title case,
                or keep them only together with harder ones.
```

## Highest score any cheat got: **1.000** (cheat 1, Python inside, jobs/2026-11-23__11-07-37)

# Attack on Ayush Singh's task (`Ayush_Kr_Singh/titlecase-go`)

Attacker: Vanam Prashanth (Day 4, 18 Nov 2026)

Target: Ayush Singh, commit `2b63c5e8563b3ae8b9f8029aa05028863c5ec277`
("Remove reward calculation formula from README") — see `TARGET.txt`. The
`tests/`, `task.toml` and `environment/` of the target were not changed. Each
cheat replaced only `solution/solve.sh` in a scratch copy and was run with
`harbor run -p <scratch-copy> -a oracle`. The reward files are in `results/`.

## How the exam works (what I read)

- The agent's room is `golang:1.23` (`environment/Dockerfile:1`) with the Python
  repo copied to `/workspace/repo` (`environment/Dockerfile:4`). `golang:1.23`
  is Debian bookworm, which ships `/usr/bin/python3` (3.11.2 in this image).
- The verifier is a separate container (`task.toml:20`,
  `environment_mode = "separate"`) with `network_mode = "public"`
  (`task.toml:21`). It receives `/workspace/repo` as an artifact
  (`task.toml:2`). Its image is `golang:1.23` plus `uv`/`uvx`
  (`tests/Dockerfile:1-3`), and the whole `tests/` folder is copied into
  `/tests/` (`tests/Dockerfile:5`), including `tests/data/hidden_expected.txt`.
  `uvx` downloads its own CPython (3.13) to run the checks.
- **build** (weight 1, `tests/checks/build.py:8-15`): `go build ./...` exits 0.
  Not tied to any correct answer.
- **no_python** (weight 1, `tests/checks/no_python.py:8-19`): no file matching
  the glob `*.py` exists under `/workspace/repo` (`rglob("*.py")`, line 8) and
  `go build ./...` exits 0. Not tied to any correct answer.
- **behaviour** (weight 4, `tests/checks/behaviour.py:10-41`): it builds the
  agent's program with `go build -o /tmp/titlecase_verifier_bin .`
  (`behaviour.py:11-17`), runs it **inside the verifier container** with
  `hidden_inputs.txt` on stdin (`behaviour.py:21-32`), and scores the share of
  output lines equal to `hidden_expected.txt` (`behaviour.py:36-41`).
- Weights are `build = 1.0, no_python = 1.0, behaviour = 4.0`
  (`tests/checks/reward.toml:13`), so
  `reward = (build + no_python + 4 * behaviour) / 6`.
- Every component uses `aggregation = "all-pass"`
  (`tests/checks/reward.toml:2,5,8`), so `behaviour` only scores when it is an
  exact **1.0** on the hidden set; any partial match counts as 0.
- The visible and hidden inputs share **0** lines (`comm -12` of the sorted
  `tests/data/inputs.txt` and `tests/data/hidden_inputs.txt`). A memorised copy
  of the visible answers is worth nothing on the hidden exam.

## Cheat 1 — Read the exam

```
What it does:   A Go program with no titlecase code. At run time it walks the disk
                (/tests, /solution, /logs, home folders) for *inputs.txt / *expected.txt
                pairs, builds an input->answer map, and prints the stored answer for each
                stdin line (echoes anything not found). solve.sh also deletes every .py file.
Score:          reward 1.0  (build 1.0, no_python 1.0, behaviour 1.0)
Job folder:     scratch/jobs/2026-11-18__20-02-46
Why it worked:  tests/checks/behaviour.py:21-32 runs the agent's binary inside the verifier
                container, where tests/Dockerfile:5 (COPY . /tests/) has placed
                tests/data/hidden_expected.txt. The verifier sets no USER, so the binary runs
                as root with no sandbox and reads the answer file. A solve-time probe in the
                cheat logged "missing: /tests" and found no answer files, which confirms the
                answers are NOT reachable while the agent is solving — only at grading time.
How to fix:     Run the agent's binary as an unprivileged user that cannot read /tests (e.g.
                chmod 700 /tests, or drop privileges before behaviour.py:27 runs the binary),
                or load the answers into memory in the grader and remove /tests/data before
                running the binary, passing only the inputs on stdin.
```

## Cheat 2 — Python inside

```
What it does:   Copies the original titlecase/__init__.py to engine/titlecase.txt, embeds it
                in a Go wrapper with //go:embed, and at run time runs that embedded source with
                the image's python3, piping stdin through the original titlecase(). No port at
                all; every .py file is deleted. The wrapper pins /usr/bin/python3 explicitly.
Score:          reward 1.0  (build 1.0, no_python 1.0, behaviour 1.0)
Job folder:     scratch/jobs/2026-11-18__22-57-52
Why it worked:  Python is present in both rooms: environment/Dockerfile:1 (golang:1.23 = Debian,
                has /usr/bin/python3) and tests/Dockerfile:1-3 (golang:1.23 + uvx). no_python only
                looks for files named *.py (tests/checks/no_python.py:8), so Python code embedded
                under another name and run through python3 passes. One catch: the verifier runs
                under uvx, which puts a newer python3 (3.13) first on PATH, and titlecase's output
                differs there by ~22 lines (behaviour 0.989). Because reward.toml:8 is all-pass,
                0.989 would score 0, so the wrapper pins /usr/bin/python3 (3.11.2) to get an
                exact 1.0. That version sensitivity is itself a flaw: the frozen answers assume
                one interpreter, which instruction.md never states.
How to fix:     Build the agent room from golang:1.23-alpine without Python and run the verifier
                in a sandbox with no python3 on PATH; also fail no_python if the repo or binary
                contains Python source (e.g. grep for "def titlecase" / "import regex", match .py
                case-insensitively). State the interpreter mode (re vs regex) in instruction.md.
```

## Cheat 3 — Build trick

```
What it does:   Deletes every .py file and writes an empty but valid Go program (func main() {})
                with no titlecase logic. go build ./... and go build -o bin . both succeed; the
                binary reads nothing and prints nothing.
Score:          reward 0.3333  (build 1.0, no_python 1.0, behaviour 0.0)
Job folder:     scratch/jobs/2026-11-18__23-20-39
Why it worked:  build and no_python are scored on their own and never check a correct answer:
                tests/checks/build.py:8-15 and tests/checks/no_python.py:12-19 check only that
                go build exits 0. So an empty binary with no .py files collects 2 of 6 points
                = 0.333 for zero functionality. behaviour scored 0 because the empty binary
                produces no output (behaviour.py:36-41), and all-pass (reward.toml:8) needs an
                exact 1.0. 0.333 is double the cheat ceiling of 0.167 the task author documented.
How to fix:     Do not award build/no_python independently of behaviour: gate their weight behind
                a minimum behaviour score, or fold them into the behaviour check so a binary that
                emits nothing earns nothing. At minimum, require that the program reads stdin and
                writes a matching number of output lines before build/no_python pay out.
```

## Highest score any cheat got

**1.0** (cheat 1 and cheat 2: a full score with no titlecase port at all).

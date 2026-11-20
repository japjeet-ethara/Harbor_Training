# Attack on Vanam Prashanth's task (`VanamPrashanth/titlecase-go`)

Attacker: Mohammad Adnan (Day 4, 18 Nov 2026)

Target: `https://github.com/japjeet-ethara/Harbor_Training`, commit
`9610c2fc5f5228126512032ecaddd6124812ec4a` (see `TARGET.txt`; on branch `training-3` the task's
`tests/`, `task.toml` and `environment/` are identical, only its README differs). The tests, `task.toml` and
`environment/` were not changed. Each cheat replaced only `solution/solve.sh` in a scratch copy and
was run with `harbor run -p <scratch-copy> -a oracle`. The reward files are in `results/`.

## How the exam works (what I read)

- The agent's room is `golang:1.23` (`environment/Dockerfile:1`) with the Python repo at
  `/workspace/repo` (`environment/Dockerfile:3`). `golang:1.23` is Debian bookworm, which ships
  `python3`.
- The verifier is a separate container (`task.toml:22`, `environment_mode = "separate"`). It gets
  `/workspace/repo` as an artifact (`task.toml:2`). Its image is `python:3.12-slim` plus Go
  (`tests/Dockerfile:1-5`), and the whole `tests/` folder is copied into `/tests/`
  (`tests/Dockerfile:24`), including `tests/data/hidden_expected.txt`.
- **build** (weight 1, `tests/build.py:26-33`): `go build ./...` passes.
- **no_python** (weight 1, `tests/no_python.py:25-44`): `go build ./...` passes and no file
  named `*.py` exists under `/workspace/repo`. It is not tied to any correct answer.
- **behaviour** (weight 4, `tests/behaviour.py:58-129`): it builds the agent's program, then runs
  it **inside the verifier container** with `hidden_inputs.txt` on stdin (`tests/behaviour.py:100-108`)
  and scores the share of lines equal to `hidden_expected.txt` (`tests/behaviour.py:118-129`).
- The visible and hidden inputs share **73** lines (`comm -12` of the sorted files).

## Cheat 1 — Read the exam

```
What it does:   A Go program with no titlecase code. At run time it looks for
                /tests/data/hidden_expected.txt (and similar paths) and prints it line by line.
                solve.sh also deletes every .py file.
Score:          reward 1.0  (build 1, no_python 1, behaviour 1.0)
Job folder:     jobs/2026-11-18__14-54-11
Why it worked:  tests/behaviour.py:100-108 runs the agent's binary inside the verifier container,
                where tests/Dockerfile:24 (COPY . /tests/) has put tests/data/hidden_expected.txt.
                The binary runs with the grader's own permissions and no sandbox (tests/Dockerfile
                sets no USER, so the verifier runs as root), so it can read the answer file.
How to fix:     Run the agent's binary as an unprivileged user that cannot read /tests (chmod 700
                /tests first), or copy only the inputs into a directory the binary can see and keep
                the answers in memory in the grader.
```

## Cheat 2 — Python inside

```
What it does:   Renames titlecase/__init__.py to orig_titlecase.txt, embeds it in a Go wrapper
                with go:embed, and at run time pipes stdin through `python3 -c` running the original
                titlecase(). No port at all; every .py file is deleted.
Score:          reward 1.0  (build 1, no_python 1, behaviour 1.0)
Job folder:     jobs/2026-11-18__14-57-36
Why it worked:  Python is present in both rooms: environment/Dockerfile:1 (golang:1.23 = Debian,
                has /usr/bin/python3) and tests/Dockerfile:1 (python:3.12-slim). no_python only
                looks for files named *.py (tests/no_python.py:40), so Python code under another
                name, called through python3, passes.
How to fix:     Build the agent room from golang:1.23-alpine without Python, run the binary in a
                verifier sandbox without python3 on PATH, and also fail no_python if the binary or
                the repo contains Python source (e.g. grep for "def titlecase" / "import regex").
```

## Cheat 3 — Lookup table + half port + delete trick

```
What it does:   Embeds the VISIBLE inputs.txt -> expected.txt table. A known input prints the stored
                answer; anything else gets a "half port" (capitalise each word, small words lower
                case unless first/last). No real titlecase rules. All .py files are deleted.
Score:          reward 0.728  (build 1, no_python 1, behaviour 0.592)
Job folder:     jobs/2026-11-18__15-00-01
Why it worked:  (a) no_python pays for deleting files: tests/no_python.py:25-44 checks only build +
                no *.py, never a correct answer, so 2 of 6 points come for free. (b) 73 hidden
                inputs also appear in the visible file, so the lookup table answers them exactly.
                (c) The hidden inputs are mostly plain lower-case words (e.g. "music vs street",
                "morning a house history jones"), so the naive rule plus the lookup table together
                match 59.2% of the hidden lines; the exam has few weird inputs (McX, initials, URLs,
                apostrophes, subphrases).
How to fix:     Pay no_python only if behaviour > 0 on hidden cases; remove hidden inputs that occur
                in the visible file; add many more inputs that need the real rules, so a half port
                scores near 0.
```

## Highest score any cheat got

**1.0** (cheat 1 and cheat 2: a full score with no titlecase port at all).

## Day 6 — re-attack on Vanam's hardened task

Target: `training-3/VanamPrashanth/task/titlecase-go` at commit `2702d02` (hardened; his proof commit
`c8600f1` only adds reports). Exported with `git archive` (LF endings), tests/environment untouched.
Same method as Day 4: `harbor run -p <copy with the cheat as solution/solve.sh> -a oracle`.

| Cheat | Day 4 | Day 6 | Components | Job folder |
|---|---|---|---|---|
| 1 read the exam | 1.0 | **0.1667** | build 1, no_python 0, behaviour 0 | `jobs/2026-11-20__15-32-55` |
| 2 Python inside | 1.0 | **0.1667** | build 1, no_python 0, behaviour 0 | `jobs/2026-11-20__15-34-13` |
| 3 lookup + half port | 0.728 | **0.1667** | build 1, no_python 0, behaviour 0 | `jobs/2026-11-20__15-35-25` |
| 4 (new) reference mount scan | — | **0.1667** | build 1, no_python 0, behaviour 0 | `jobs/2026-11-20__15-36-38` |

Cheat 4 is Charitra's Day 6 probe (`cheat4/solve.sh`): look for a Go port under `/solution/go`,
`/opt/python-titlecase`, … and copy it. Vanam's port lives only inside `solution/solve.sh`, so it finds
nothing and falls back to echoing the input. Reward files: `results/day6-cheat1..4-reward.json`.

**Verdict:** every cheat is below 0.2; highest score now 0.1667 (was 1.0). The 0.1667 is only the
build point. Looked at but not tried: a cgo `.incbin` of the answers at build time (the verifier image
`python:3.12-slim` has no C compiler, and a fresh 2,000-title seed per run would beat a lookup anyway).
Remaining weak spot I noticed: the agent image is `golang:1.23` (Debian, ships `python3`), so an agent
can still *use* Python while working; the grader's empty jail stops it at grading time.

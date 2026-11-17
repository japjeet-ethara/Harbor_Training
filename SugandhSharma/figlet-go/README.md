# figlet-go

A Harbor task by sugandhsharma (Practice Task 2).

[pyfiglet](https://github.com/pwaller/pyfiglet) draws a short text in giant letters made of slashes and
underscores. The task: replace it with a Go program that draws the same thing, byte for byte, for every input
and every option. The task is graded against answers that were frozen by running the original Python code.

## Results

| Run | What it is | Reward | Secret |
|---|---|---|---|
| oracle | the reference solution (`solution/`) | **1.0** | drawn by the twin |
| nop | an agent that does nothing | **0.0** | "No secret for you. Yet." |
| cheat | a Go program that looks its arguments up in the visible cases (`cheat/`) | **0.1667** (below 0.2) | "No secret for you. Yet." |

Real terminal captures of the three runs: [oracle](screenshots/oracle.png), [nop](screenshots/nop.png),
[cheat](screenshots/cheat.png). The reward files and verifier logs are in `results/`:

```
oracle  {"behaviour": 1, "build": 1, "no_python": 1, "reward": 1}
nop     {"behaviour": 0, "build": 0, "no_python": 0, "reward": 0}
cheat   {"behaviour": 0, "build": 1, "no_python": 0, "reward": 0.1667}
```

## Two lines

**Which smushing rule broke the agent most?** None at the first full comparison (2000 visible, 2000 hidden
and 40,000 extra cases all matched), because the port follows `FigletBuilder` line by line; the part that
needs the most care is the overlap in right-to-left mode together with `-j`, since both add spaces on the
left, and the first set of hidden cases was the weak spot: it let 12 deliberately broken ports through that a
larger random set caught (entries of the `-F` and `-r` tables), until two more fonts were added to the cases.

**Which Docker trap did I hit?** `harbor task init` (0.25.0) creates a separate verifier with a Python image
in `tests/Dockerfile`, but this room has no Python and the page asks for the shared verifier, so that file
had to go and the grader had to be a Go program; the two traps the page warns about are real too
(`golang:1.23` contains `/usr/bin/python3` and git, and the Alpine image has no `bash`).

## The room

`environment/Dockerfile` has two stages. The six rules of the page, with what the built image shows:

| # | Rule | How it is met | Check |
|---|---|---|---|
| D1 | Two stages | stage `source` (a git image) clones pyfiglet; stage 2 copies only `/src` | `command -v git` finds nothing in the room |
| D2 | No Python | stage 2 is `golang:1.23-alpine` | `NO_PYTHON` |
| D3 | The original's own setup | stage 1 does the Makefile step: `mkdir pyfiglet/fonts && cp pyfiglet/fonts-standard/* pyfiglet/fonts/` | 72 files in `pyfiglet/fonts` |
| D4 | A normal user | `adduser -D -u 1000 player`, `COPY --chown=player:player`, `USER player` | `whoami` gives `player`, `touch x` works |
| D5 | Pinned images | both images are pinned by tag and by digest | see the two `FROM` lines |
| D6 | Harbor can run in it | `apk add --no-cache bash` | `/bin/bash` |

```
docker build -t figlet-room environment/
docker run --rm figlet-room sh -c 'whoami; pwd; ls pyfiglet/fonts | wc -l; command -v python3 || echo NO_PYTHON; command -v bash; touch x && echo CAN_WRITE'
```

prints `player`, `/workspace/repo`, `72`, `NO_PYTHON`, `/bin/bash`, `CAN_WRITE`.

`task.toml`: `[agent] user = "player"`, 3600 seconds; `[verifier]` 900 seconds, `environment_mode = "shared"`;
`[environment] network_mode = "public"`, build timeout 900 seconds. `harbor lint figlet-go` gives one finding,
the expected `shared-verifier`.

## How it is graded

`tests/test.sh` runs `cd /tests && go run grade.go`. The grader is a Go program because the room has no
Python; it uses the standard library only and downloads nothing. It writes `/logs/verifier/reward.json`.

| Check | Weight | Score |
|---|---|---|
| `build` | 1 | 1 if `go build ./...` and `go build -o /tmp/figlet .` pass in `/workspace/repo` (offline), else 0 |
| `no_python` | 1 | 1 only if the build passed, no `.py` file is left, the font files the cases use are still inside the repository, and at least one hidden case is right; else 0 |
| `behaviour` | 4 | share of the 2000 hidden cases whose standard output equals the frozen answer exactly (5 seconds per case, started from another working directory) |

reward = (build + no_python + 4 x behaviour) / 6. By hand: nothing done 0; build only 1/6 = 0.1667; perfect 1.0.

`no_python` is tied to a right answer on purpose: the cheat builds and deletes the `.py` files, and would
otherwise get 2/6 = 0.33.

**The secret.** If behaviour is exactly 1.0, the grader decodes `tests/secret.b64`, lets the twin draw it with
`-f slant`, and prints it after `*** SECRET UNLOCKED ***`. Otherwise it prints `No secret for you. Yet.`
The secret is not in the instruction and not in the image.

## The cases

`tests/gen.py` (seed 7) writes `tests/data/visible.jsonl` and `tests/data/hidden.jsonl`, 2000 cases each, one
JSON line per case: `{"args": [...], "out": "..."}`. Every `out` is what `main()` of the original wrote to
standard output for those arguments. No case is in both files.

- Fonts: the eight of the page (standard, slant, small, big, mini, banner, shadow, script), plus `term` and
  `ivrit` in about one case in seven. `term` prints every character as itself, so it is the only way most of
  the `-F` and `-r` tables decide a case; `ivrit` is the only standard font whose header says right-to-left.
- Widths 10, 20, 40, 60, 80, 120; every value of `-j` and `-D`; `-r`, `-F`, `-s`, `-n` each in one case of four.
- Texts: ordinary words, pieces that touch (`|_|`, `/\`, `[]`, `><` ...), double spaces, long sentences that
  wrap, long words with no blank, Latin-1 letters, characters the font does not have, line breaks, and 70
  two-character texts found by `dev/find_rare_pairs.py`, each of which depends on one small part of the rules.
- Hidden cases: about 22 percent right-to-left, 23 percent with width 10 or 20, 31 percent centred or right.
- Left out: cases where the original stops with an error (a letter wider than the window), never finishes
  (a letter exactly as wide as the window) or draws nothing.

## How to reproduce

Needs Docker, Harbor 0.25 and Python 3. pyfiglet must be in a folder next to this one, at the pinned commit,
with its font setup done:

```bash
git clone https://github.com/pwaller/pyfiglet && cd pyfiglet
git checkout 255827efbc09d662875dad50fa0edc1e1263bf45
mkdir -p pyfiglet/fonts && cp pyfiglet/fonts-standard/* pyfiglet/fonts/ && cd ..
```

On Windows use Git Bash and run `export PYTHONUTF8=1 PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1` first.

```bash
# 1. the cases (run inside figlet-go; the same files on every run)
python tests/gen.py

# 2. the three runs (run from the folder that holds figlet-go)
harbor run -p figlet-go -a oracle -o jobs --job-name fig-oracle -y
harbor run -p figlet-go -a nop -o jobs --job-name fig-nop -y

cp -r figlet-go figlet-go-cheat && rm -rf figlet-go-cheat/solution && mkdir figlet-go-cheat/solution
cp figlet-go/cheat/solve.sh figlet-go/tests/data/visible.jsonl figlet-go-cheat/solution/
harbor run -p figlet-go-cheat -a oracle -o jobs --job-name fig-cheat -y
rm -rf figlet-go-cheat

# 3. the rewards and the secret
cat jobs/fig-*/*/verifier/reward.json jobs/fig-*/*/verifier/test-stdout.txt
```

The cheat is run on a copy of the task folder, so the real solution is never overwritten.

## The tests were tested

Run inside `figlet-go`, after `docker build -t figlet-room environment/`. On Linux or a Mac write `$(pwd)` for
`$(pwd -W)` and leave out `MSYS_NO_PATHCONV=1`.

```bash
# the reference solution against the frozen answers, built in the room as the user player
MSYS_NO_PATHCONV=1 docker run --rm -v "$(pwd -W):/task:ro" figlet-room bash /task/dev/build_and_compare.sh

# the reference solution against the original on 40,000 more cases, over all 67 standard fonts
python dev/fuzz.py .. ../scratch 40000
MSYS_NO_PATHCONV=1 docker run --rm -v "$(pwd -W):/task:ro" -v "$(cd ../scratch && pwd -W):/fuzz:ro" \
  figlet-room bash /task/dev/build_and_compare.sh /fuzz/fuzz.jsonl

# broken variants of the solution, one small change each: do the hidden cases notice?
python dev/mutants.py . ../scratch/mut && head -3000 ../scratch/fuzz.jsonl > ../scratch/fuzz_small.jsonl
MSYS_NO_PATHCONV=1 docker run --rm -v "$(pwd -W):/task:ro" -v "$(cd ../scratch && pwd -W):/scratch" \
  figlet-room bash /task/dev/run_mutants.sh
```

Results: 2000 of 2000 visible and 2000 of 2000 hidden cases match; 40,000 of 40,000 extra cases match.
Of 77 broken variants, the hidden cases catch all 66 that change any output (the weakest on 1 case, most on
dozens to hundreds); the other 11 change nothing on any case, because no standard font uses smushing rules 5
and 6 or has a letter narrower than 2 columns (`dev/mutation_report.txt`).

## The page's secret

Inside the built image, with the oracle's Go code:

```
$ cd /workspace/repo && go build -o /tmp/figlet . && /tmp/figlet -f slant "$(echo Z28gdG91Y2ggZ3Jhc3M= | base64 -d)"
                   __                   __                                 
   ____ _____     / /_____  __  _______/ /_     ____ __________ ___________
  / __ `/ __ \   / __/ __ \/ / / / ___/ __ \   / __ `/ ___/ __ `/ ___/ ___/
 / /_/ / /_/ /  / /_/ /_/ / /_/ / /__/ / / /  / /_/ / /  / /_/ (__  |__  ) 
 \__, /\____/   \__/\____/\__,_/\___/_/ /_/   \__, /_/   \__,_/____/____/  
/____/                                       /____/                        
```

The letters come out clean, and they are byte for byte what the original draws (`results/page-secret.txt`).

## Source and licence

- Repository: https://github.com/pwaller/pyfiglet
- Commit: `255827efbc09d662875dad50fa0edc1e1263bf45` (2026-08-02), package version 1.0.4
- Licence: MIT, "Copyright (c) 2007-2018 Christopher Jones, Stefano Rivera, Peter Waller, and various
  contributors". The image fetches the project from GitHub at that commit; no copy of it is in this folder.
- Only the fonts of `fonts-standard/` are used; `fonts-contrib/` is removed in stage 1.
- `NOTES.md` has the font setup step, the six smushing rules with examples, the eight options and the rare cases.

## Layout

```
figlet-go/
  README.md                 this file
  NOTES.md                  source, licence, font setup, six smushing rules, eight options, rare cases
  instruction.md            the only text the solving agent reads
  task.toml                 agent user "player", shared verifier, limits
  environment/
    Dockerfile              two stages: fetch pyfiglet at the pinned commit; the room (Alpine Go, bash, player)
  solution/
    solve.sh                puts the Go port into the repository, keeps the fonts there, removes the Python code
    go.mod  main.go  font.go  render.go  pystr.go      the Go port, standard library only
  tests/
    test.sh                 runs the grader
    grade.go                the three checks, reward.json, the secret
    secret.b64              the secret, base64
    gen.py                  makes the two case files from the original code (fixed seed)
    data/                   visible.jsonl, hidden.jsonl (2000 cases each)
  cheat/
    solve.sh                the cheat that must score below 0.2
  dev/
    build_and_compare.sh  compare.go      first five cases where the port differs from the frozen answers
    fuzz.py                               40,000 extra cases with answers from the original
    find_rare_pairs.py                    finds the two-character texts each small part of the rules decides
    mutants.py  run_mutants.sh  mutation_report.txt
  results/                  reward.json and verifier log of the three runs, the page's secret
  screenshots/              oracle.png, nop.png, cheat.png (terminal captures)
```

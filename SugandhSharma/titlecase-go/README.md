# titlecase-go

A Harbor task by sugandhsharma.

The Python library [python-titlecase](https://github.com/ppannuto/python-titlecase) turns `the lord of the rings`
into `The Lord of the Rings`. The task: replace it with a Go program that gives the same output, byte for byte,
for every line. The task is graded against answers that were frozen by running the original Python code.

## Results

| Run | What it is | Reward |
|---|---|---|
| oracle | the reference solution (`solution/`) | **1.0** |
| nop | an agent that does nothing | **0.0** |
| cheat | a Go program that only prints the visible answer sheet (`cheat/`) | **0.1667** (below 0.2) |

Screenshots: [oracle](screenshots/oracle.png), [nop](screenshots/nop.png), [cheat](screenshots/cheat.png).

The reward files of the three runs are in `results/`:

```
oracle  {"behaviour": 1.0, "build": 1.0, "no_python": 1.0, "reward": 1.0}
nop     {"behaviour": 0.0, "build": 0.0, "no_python": 0.0, "reward": 0.0}
cheat   {"behaviour": 0.0, "build": 1.0, "no_python": 0.0, "reward": 0.1667}
```

## Two lines

**Which rules did the agent get wrong most?** The word rules were right at the first full comparison (2000
visible, 2000 hidden and 200,000 extra random titles all matched); the mistakes were around them: the build
check gave 0 twice because the old `titlecase` folder was still in the repository, and the first hidden set
let 29 of 115 deliberately broken ports through, mostly ports with one character missing from the punctuation
list.

**What would I add to make the task harder?** Titles with letters outside ASCII (Python and Go disagree on what
a letter and an upper-case form are), no network for the agent so it cannot run the original next to its port,
and `no_python` paid only when behaviour is above a mark, because a program that only copies its input already
scores 0.36.

## How it is graded

Reward Kit, weighted mean of three checks. Each check is one folder under `tests/`.

| Check | Weight | Score |
|---|---|---|
| `build` | 1 | 1 if `go build ./...` passes in `/workspace/repo` (offline, Go 1.23), else 0 |
| `no_python` | 1 | 1 if no `.py` file is left under `/workspace/repo` and the build passes, else 0 |
| `behaviour` | 4 | share of the 2000 hidden titles whose output equals the frozen answer exactly |

reward = (build + no_python + 4 x behaviour) / 6.

The verifier runs in its own container (`environment_mode = "separate"`), so the agent never sees `tests/`.
The behaviour check reads only `hidden_inputs.txt` and `hidden_expected.txt`. The visible pair
(`inputs.txt`, `expected.txt`) is for building the reference solution, and it shares no title with the hidden
pair, which is why the cheat scores 0 on behaviour.

## How to reproduce

Needs Docker, Harbor (tested with 0.20.0) and Python 3. The original project must be in a folder next to this
one: `git clone https://github.com/ppannuto/python-titlecase` and
`git -C python-titlecase checkout 42f43e2de55bf003b286c6f8e8d8b2d26676a167`.
On Windows use Git Bash and run `export PYTHONUTF8=1 PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1` first.

```bash
# 1. the answer sheets (run inside titlecase-go; writes tests/data; the same files on every run)
python tests/gen.py

# 2. the three runs (run from the folder that holds titlecase-go)
harbor run -p titlecase-go -a oracle -o jobs --job-name oracle -y
harbor run -p titlecase-go -a nop -o jobs --job-name nop -y

cp -r titlecase-go titlecase-go-cheat
rm -rf titlecase-go-cheat/solution && mkdir titlecase-go-cheat/solution
cp titlecase-go/cheat/solve.sh titlecase-go/tests/data/expected.txt titlecase-go-cheat/solution/
harbor run -p titlecase-go-cheat -a oracle -o jobs --job-name cheat -y
rm -rf titlecase-go-cheat

# 3. the rewards
cat jobs/oracle/*/verifier/reward.json jobs/nop/*/verifier/reward.json jobs/cheat/*/verifier/reward.json
```

The cheat is run on a copy of the task folder, so the real solution is never overwritten.

## The tests were tested

Run inside `titlecase-go`. On Windows (Git Bash) keep the commands as they are; on Linux or a Mac write
`$(pwd)` for `$(pwd -W)` and leave out `MSYS_NO_PATHCONV=1`.

```bash
mkdir -p ../scratch

# the reference solution against the original on about 200,000 more titles
python dev/fuzz.py .. ../scratch
MSYS_NO_PATHCONV=1 docker run --rm -v "$(pwd -W):/task" -v "$(cd ../scratch && pwd -W):/fuzz" -w /task/solution \
  golang:1.23 bash -c 'go build -o /tmp/tc . && /tmp/tc < /fuzz/fuzz_inputs.txt > /fuzz/fuzz_actual.txt'
python dev/compare.py ../scratch/fuzz_actual.txt ../scratch/fuzz_inputs.txt ../scratch/fuzz_expected.txt

# 115 broken variants of the solution, one small change each: does the hidden set notice?
python dev/mutants.py . ../scratch/mut
MSYS_NO_PATHCONV=1 docker run --rm -v "$(pwd -W):/task:ro" -v "$(cd ../scratch && pwd -W):/fuzz" \
  golang:1.23 bash /task/dev/run_mutants.sh
python dev/score_mutants.py ../scratch/mut tests/data/hidden_expected.txt tests/data/expected.txt \
  ../scratch/fuzz_expected.txt
```

Result: 200,000 of 200,000 lines match. Of the 115 variants, 114 get at least 3 hidden lines wrong and one has
no effect on any output (`dev/mutation_report.txt`).

## Source and licence

- Repository: https://github.com/ppannuto/python-titlecase
- Commit: `42f43e2de55bf003b286c6f8e8d8b2d26676a167` (2024-04-05), package version 2.4.1
- Licence: MIT, "Copyright (c) 2021 Patrick William Pannuto" (`environment/python-titlecase/LICENSE.txt`)
- `environment/python-titlecase/` is an unchanged copy of that commit without its `.git` and `.github` folders.
- The reference is `titlecase()` with default arguments on the code path without the optional `regex` package.
  `NOTES.md` has the rules, real examples and the surprises.

## Layout

```
titlecase-go/
  README.md                 this file
  NOTES.md                  source, licence, reference mode, 17 rules with examples, surprises, what went wrong
  instruction.md            the only text the solving agent reads
  task.toml                 settings: separate verifier, artifacts = ["/workspace/repo"], limits
  environment/
    Dockerfile              FROM golang:1.23, the Python project copied to /workspace/repo
    python-titlecase/       the original at the commit above
  solution/
    solve.sh                puts the Go port into the repository and removes the Python code
    go.mod  main.go         the Go port, standard library only
  tests/
    Dockerfile              the verifier image: Go 1.23 and Reward Kit 0.2.4
    test.sh                 runs Reward Kit, which writes /logs/verifier/reward.json
    reward.toml             weights 1, 1, 4, weighted mean
    build/check.py          check 1
    no_python/check.py      check 2
    behaviour/check.py      check 3
    gen.py                  makes the four data files from the original code (fixed seed)
    data/                   inputs.txt, expected.txt, hidden_inputs.txt, hidden_expected.txt (2000 lines each)
  cheat/
    solve.sh                the cheat that must score below 0.2
  dev/
    compare.py              first 10 lines where an output differs from the frozen answers
    fuzz.py                 about 200,000 extra titles with answers from the original
    mutants.py  run_mutants.sh  score_mutants.py  mutation_report.txt
  results/                  reward.json and reward-details.json of the three runs
  screenshots/              oracle.png, nop.png, cheat.png
```

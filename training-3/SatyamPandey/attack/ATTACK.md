# Attack report — Yash Singla's `titlecase-go` task

Attacker: Satyam Pandey
Target:   `YashSingla/titlecase-go` at commit `9fc663cd248ac03f5224bca62d43f80b8af86b99` (also in `TARGET.txt`).
          This was Yash's practice-1 folder; his `training-3/Yash Singla/task/` did not exist yet when the attack
          started. That later copy (commit `a95d51a`) differs only by an added `.gitattributes` (`*.sh text eol=lf`);
          `tests/`, `task.toml`, `environment/` and the data are byte-identical, so every result below applies to it.
Verified: 2026-11-20, re-run from scratch (see "How this was verified").
Method:   I exported the target from git at that commit, made one copy per run, put each cheat in its
          `solution/solve.sh`, and ran `harbor run -p <copy> -a oracle`. I did not change the target's `tests/`,
          `task.toml` or `environment/`. None of the cheats contains a real titlecase port.

This report covers only the three strongest cheats. Each one gets a perfect score. The full list of
weaknesses is at the end.

---

## Baseline (unchanged target)

| Run | Reward | build | no_python | behaviour | Job folder |
|---|---|---|---|---|---|
| Yash's oracle | **1.0** | 1 | 1 | 1.0 | `jobs/2026-11-20__11-12-34` |
| nop | **0.0** | 0 | 0 | 0.0 | `jobs/2026-11-20__11-14-43` |

The grader works on an honest run. The cheats below show it can't tell an honest port from a fake one.

## Results

| Cheat | Reward | build | no_python | behaviour | Job folder |
|---|---|---|---|---|---|
| 1 Python inside | **1.0** | 1 | 1 | 1.0 | `jobs/2026-11-20__11-16-41` |
| 2 Read the exam at run time | **1.0** | 1 | 1 | 1.0 | `jobs/2026-11-20__11-18-33` |
| 3 Fetch the exam over the network | **1.0** | 1 | 1 | 1.0 | `jobs/2026-11-20__11-20-25` |

**Highest score any cheat got: 1.0** (all three).

---

## Cheat 1 — Python inside
What it does:   Copies the original `titlecase/__init__.py` to `titlecase_src.txt` and deletes every `.py` file.
                A tiny Go `main` embeds that text with `go:embed` and runs it with the `python3` already in the
                image. The Go code does no titlecasing itself.
Script:         `attack/cheat1/solve.sh`
Score:          reward 1.0  (build 1, no_python 1, behaviour 1.0)
Job folder:     `jobs/2026-11-20__11-16-41`
Why it worked:  `tests/no_python.py:9` only checks for files whose suffix is `.py`, so Python source named `.txt`
                passes. Both images are `golang:1.23` (`environment/Dockerfile:1`, `tests/Dockerfile:2`), which
                ships `/usr/bin/python3` (Python 3.11.2). `tests/behaviour.py:28-36` runs the binary with the
                full environment, so it can start any program.
How to fix:     Remove Python from both images (or use a Go-only base image). Run the binary as an unprivileged
                user with a minimal PATH. In `no_python`, also reject `os/exec`, `syscall`, `os.StartProcess` and
                embedded Python source.

## Cheat 2 — Read the exam at run time
What it does:   The Go binary has no titlecase logic. When the grader runs it, it opens
                `/tests/data/hidden_inputs.txt` and `hidden_expected.txt`, builds a map, and prints the stored
                answer for each line. Lines it can't find are echoed back unchanged.
Script:         `attack/cheat2/solve.sh`
Score:          reward 1.0  (build 1, no_python 1, behaviour 1.0)
Job folder:     `jobs/2026-11-20__11-18-33`
Why it worked:  `tests/Dockerfile:11` copies the answers to `/tests/data/`, and `tests/behaviour.py:28-36` runs
                the submitted binary in that same container, as root (uid 0), with full file access.
                Echoing alone would not explain the score: 176 of the 2,000 hidden inputs are already in their
                expected form, so pure echo matches only 8.8% of lines. Reading the answer file gets the other
                1,824.
How to fix:     Read the data into memory first, then `chmod -R 700 /tests` and run the binary as `nobody`
                (`subprocess.run(..., user="nobody", env={"PATH": "/usr/bin:/bin"}, cwd="/tmp")`).

## Cheat 3 — Fetch the exam over the network
What it does:   During the agent run, `solve.sh` uses `curl` to download `hidden_inputs.txt` and
                `hidden_expected.txt` from the public GitHub repo at the target commit. It embeds them with
                `go:embed` as a lookup table, and unknown lines are echoed back.
Script:         `attack/cheat3/solve.sh`
Score:          reward 1.0  (build 1, no_python 1, behaviour 1.0)
Job folder:     `jobs/2026-11-20__11-20-25`
Why it worked:  `task.toml:24` gives the agent `network_mode = "public"`, `curl` is in the image, and the answers
                that `tests/Dockerfile:11` treats as hidden are committed in plain text to a public repo.
How to fix:     Set `network_mode = "allowlist"` with `allowed_hosts = []` (the task needs only the Go standard
                library). Pre-install rewardkit in `tests/Dockerfile` so grading needs no network
                (`tests/test.sh:3` downloads it with `uvx`). Then grade on a new exam that was never committed.

---

## All weaknesses found

### A. Holes a cheat can use

| # | Weakness | Where | Evidence |
|---|---|---|---|
| A1 | `no_python` only checks file suffixes; Python renamed to `.txt` passes, and `python3` is in both images | `tests/no_python.py:9`, `environment/Dockerfile:1`, `tests/Dockerfile:2` | Cheat 1 → **1.0** |
| A2 | The binary under test can read `/tests/data/hidden_expected.txt` while it is graded, as root | `tests/Dockerfile:11`, `tests/behaviour.py:28-36` | Cheat 2 → **1.0** |
| A3 | The hidden answers are on public GitHub, and the agent has internet | `task.toml:24` | Cheat 3 → **1.0** |
| A4 | `build` and `no_python` both reward "it compiles" — the same `go build ./...` check twice — and together carry 2 of 6 weights. An empty Go program scores 0.333 for no work; a program that only echoes its input scores about 0.392 (176/2,000 lines already match). Both are above the 0.2 limit. | `tests/build.py:10-18`, `tests/no_python.py:11-19`, `tests/reward.toml:4` | Cheat 4 (empty program) → **0.333** (`jobs/2026-11-20__11-22-43`); echo score is computed, not a Harbor run |
| A5 | Partial credit per line rewards a weak port that knows only the easy rules | `tests/behaviour.py:44-45` | Cheat 5 (two-rule port) → **0.928**, behaviour 0.8915 = 1,783/2,000 (`jobs/2026-11-20__11-24-52`) |
| A6 | The rule "Use only the Go standard library" is never checked — no test looks at `go.mod` or imports | `instruction.md:11` | Read of `tests/` |

### B. The exam is not weird enough

| # | Weakness | Where | Evidence |
|---|---|---|---|
| B1 | The hidden exam has none of the special cases the task describes. In 2,000 hidden titles: 0 apostrophes, 0 `Mc` names, 0 slashes, 0 hyphens, 0 dashes, 0 colons, 0 periods, 0 digits, 0 non-ASCII characters, 0 internal capitals (`eBay`), and only 45 distinct words. What it does test: all-caps lines (492), a leading honorific `mr/mrs/ms/dr` (519), tabs (186), double spaces (329) and trailing spaces (172). The cause: each special case comes from a short fixed list (`tests/gen.py:33-59`), the visible set is drawn first and uses up those lists, and the hidden set excludes every visible title (`tests/gen.py:71`). | `tests/gen.py:28-59`, `:71` | Feature count on `tests/data/hidden_inputs.txt` |
| B2 | None of the brief's weird word families appear: `v1.2`, `_dream`, `Mcx-`, `ıstanbul`, non-breaking spaces | `tests/gen.py:15-21` (41-word vocabulary) | same as B1 |
| B3 | The exam passes a wrong port. Yash's own oracle is 0/2,000 wrong on his exam, but **5,435 / 50,000** wrong on a weird pool (no-regex answers), or **3,234** (regex answers). Examples (original → Yash): `v1.2`→`V1.2`, `_dream`→`_Dream`, `IF`→`If`, input `aB`: `AB`→`aB`. | `solution/solve.sh` | Local measurement, not a Harbor run |

### C. The exam is too small

| # | Weakness | Where |
|---|---|---|
| C1 | Only 2,000 hidden titles. The brief asks for a 100,000-title pool: a bug on ~16 titles out of 100,000 is missed by a 2,000-title exam about 72% of the time (0.98^16 ≈ 0.724). | `tests/data/hidden_inputs.txt`, `tests/gen.py:71` |

### D. Mode not stated

| # | Weakness | Where | Evidence |
|---|---|---|---|
| D1 | `instruction.md` never says whether the answers come from titlecase WITH or WITHOUT the optional `regex` package, which changes the output (`titlecase/__init__.py:17-23`) | `instruction.md:17` | — |
| D2 | The exam can't tell the modes apart. On Yash's 2,000 hidden titles both modes give identical answers (0 differences); on a weird pool they differ on **2,358 / 50,000**. | `tests/data/hidden_expected.txt` | `analysis/run_tc.py` + `analysis/cmp.py` |
| D3 | The answers were frozen by one run of the original, not two runs that keep only stable answers | `tests/gen.py:79` | — |

### E. Grading depends on the network

| # | Weakness | Where |
|---|---|---|
| E1 | `tests/test.sh` downloads rewardkit with `uvx` at grading time, so the verifier needs internet. This blocks the obvious fix for Cheat 3 (turning the network off) unless rewardkit is pre-installed. | `tests/test.sh:3`, `tests/Dockerfile:7` |

---

## How this was verified (2026-11-20)

1. Confirmed `9fc663c` is the only commit touching `YashSingla/titlecase-go`, and that it is unchanged at `HEAD`.
2. Exported the task with `git -c core.autocrlf=false archive 9fc663c`. No file has CRLF line endings, and the
   export is identical to `attack/target/`.
3. Made 7 fresh copies (oracle, nop, cheat1-5; cheats 4-5 support A4-A5), each with the original `tests/`, `task.toml` and `environment/`.
4. Ran each with Harbor (`-a oracle` for the cheats, `-a nop` for nop). Raw scores are in
   `attack/results/cheatN-reward.json` (plus `oracle-` and `nop-reward.json`), with the per-check breakdown in `<run>-reward-details.json`.
   (`jobs/` is git-ignored, so the job folders are not in the repo.)
5. Checked inside `golang:1.23`: `/usr/bin/python3` (3.11.2) and `/usr/bin/curl` exist, and the default user is root.
6. Re-measured B1, B3, C1 and D2 with the scripts in `attack/analysis/`:
   - `weird_pool.py 50000 1 pool.txt` makes the 50,000-title pool.
   - `run_tc.py` runs the original titlecase: twice without `regex` inside `golang:1.23` with `--network none`
     (0 differences between the runs), and once with `regex` installed.
   - Yash's port: his `solution/solve.sh` run in `golang:1.23` (`--network none`), built with `go build`, fed `pool.txt`.
   - `cmp.py <expected> <got>` gives a byte-exact count of wrong lines.

### Corrections to the first version of this report (2026-11-18)

- Cheat 2 said "echoing the input alone matches 0 of 2,000 lines". The correct number is **176 of 2,000** (8.8%).
  Cheat 2's 1.0 is unaffected.
- B1 said "only plain word strings, tabs and double spaces are tested". The hidden set also has 492 all-caps lines
  and 519 lines with a leading honorific. The zero counts were correct.
- On Windows, `harbor run` crashes before running if the console is not UTF-8 (`UnicodeEncodeError` from its
  progress spinner). Set `PYTHONUTF8=1` and `PYTHONIOENCODING=utf-8` first.

---

## Day 6 — Re-attack on the hardened task

(to be filled in after Yash pushes the hardened task)

| Cheat | Day 4 score | Day 6 score | Job folder |
|---|---|---|---|
| 1 Python inside | 1.0 | | |
| 2 Read the exam | 1.0 | | |
| 3 Network fetch | 1.0 | | |
| new | — | | |

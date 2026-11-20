# HARDEN.md — Satyam Pandey, titlecase-go (Day 5)

Attacker: Neha Gaur (`training-3/NehaGaur/attack/ATTACK.md`, attacked commit `626c617`).
All job folders are under `SatyamPandey/jobs/` (not pushed); their `reward.json` and
`reward-details.json` are copied into `harden-results/`.

## Step 5.1 — Neha's cheats re-run on my task BEFORE the fix

Run on a scratch copy of my unchanged practice-1 task (same tests, same data as the
Day 4 copy), with each cheat as `solution/solve.sh` (`harbor run -a oracle`).

| Cheat | Neha's score | My re-run | build / no_python / behaviour | Job folder |
|---|---|---|---|---|
| 1 Lookup table | 0.3333 | **0.3523** | 1 / 1 / 0.0285 | `jobs/2026-11-20__15-23-31` |
| 2 Half port | 0.3333 | **0.4867** | 1 / 1 / 0.23 | `jobs/2026-11-20__15-25-19` |
| 3 Read the exam | 1.0 | **1.0** | 1 / 1 / 1.0 | `jobs/2026-11-20__15-27-02` |

The numbers differ for cheats 1 and 2. Both numbers are listed here. In my re-run,
`behaviour` gave cheat 1 a little credit (its "echo the input" fallback is right on
57 of 2,000 hidden titles) and gave cheat 2 23% (its simple rules are right on 460
titles). Neha's report shows `behaviour` 0.0 for both. I could not reproduce that: her
`solve.sh` files arrive with CRLF line endings on Windows, and I stripped the CR so
they run. Either way, the result was the same: all three cheats scored 0.33 or more,
and cheat 3 scored a full 1.0.

## Holes closed

Final runs on the hardened task (all fixes below, including the fresh sample). The frozen
and fresh counts are from each job's `verifier/test-stdout.txt`.

| Cheat | Before (my re-run) | Now | frozen / fresh exact | Job folder (now) |
|---|---|---|---|---|
| 1 Lookup table | 0.3523 | **0.0** | 1,508/100,000 · 224/5,000 | `jobs/2026-11-20__16-33-27` |
| 2 Half port | 0.4867 | **0.0** | 17,307/100,000 · 825/5,000 | `jobs/2026-11-20__16-35-12` |
| 3 Read the exam | 1.0 | **0.0** | 1,483/100,000 · 251/5,000 | `jobs/2026-11-20__16-36-53` |

Proofs on the final task: **oracle 1.0** (100,000/100,000 and 5,000/5,000,
`jobs/2026-11-20__16-30-09`), **nop 0.0** (`jobs/2026-11-20__16-32-04`).
Earlier versions of the task gave the same 1.0 / 0.0 / 0.0 results: before the fresh
sample (`15-03-32`, `15-10-44`, `15-12-22`, `15-14-14`, `15-15-52`), and with the
unmutated fresh sample (`15-44-11` to `15-58-51`).

**Cheat 1 and Cheat 2 — fix: `build` and `no_python` give no points on their own.**
The old `tests/reward.toml:7` used the weights `build 1, no_python 1, behaviour 4`. So any
Go program that compiled after the `.py` files were deleted got 2/6 = 0.33 for free. Now
`tests/checks/reward.toml` sets the weights to `build 0, no_python 0, behaviour 1`. The
two checks still run and still appear in `reward-details.json`, which helps with
diagnosis. Their conditions are now a gate inside `behaviour`, which returns 0 if the
rules fail or the program does not build.
`behaviour` also scores more strictly: `max(0, (share − 0.9) / 0.1)`. The task asks for
byte-exact output, so a port only earns points once it is right on more than 90% of
titles. On the new exam, the half port is right on 17.3% of titles and the echo fallback
on 1.5%, so both get 0.

**Cheat 3 — fix: the agent's program cannot read any file while it is graded.**
It used to work because the old `tests/behaviour.py:37` ran the binary as root in the
same container as `/tests/data/hidden_expected.txt`. Now `tests/checks/behaviour.py`:
1. reads the inputs and answers into memory first, then builds the binary into a
   root-only temp folder;
2. runs it with Reward Kit's own `rk.Worker`, which uses a fresh unprivileged UID and an
   empty environment. `/tests`, `/logs/verifier` and `/workspace` are locked to mode 0700,
   and the worker refuses to start if it can still access them. Leftover processes are
   killed. The binary gets the titles on stdin only.

Also, `tests/test.sh` now has Reward Kit write its result into a root-only `mktemp -d`
folder, and copies it into `/logs/verifier` only afterwards. A file the program might
drop in `/logs/verifier` (for example a fake `reward.txt`) can therefore never count.

**Extra probes (my own, `harden-probes/`) — so a Day 6 re-attack has less room:**

| Probe | What it tries | Without the fix | Now | Why it fails now | Job folder |
|---|---|---|---|---|---|
| probe-answers | cheat 3 updated for the new file name: reads `/tests/data/answers.txt`, then searches the whole disk | would be 1.0 | **0.0** | sandbox: it found nothing and echoed (1,483/100,000) | `jobs/2026-11-20__16-38-35` |
| probe-python | "Python inside" with no `os/exec`: the original source embedded in Go and run with the verifier's `python3` via `os.StartProcess` | 96.95% right (measured locally) → ~0.70 | **0.0** | rules: "forbidden identifier" | `jobs/2026-11-20__16-40-21` |
| probe-cgi | same, but through the standard package `net/http/cgi` (which uses `os/exec` inside), with no forbidden name | 96.9% right (measured locally) → ~0.69 | **0.0** | rules: "depends on os/exec" | `jobs/2026-11-20__16-42-00` |
| probe-lookup | cheat 1 upgraded: all 100,000 **public** answers embedded with `go:embed`, echo for anything else | frozen 100,000/100,000 → **1.0** | **0.0** | fresh sample: 232/5,000 | `jobs/2026-11-20__16-44-04` |
| probe-wordtable | smartest lookup: exact lines from the public answers; otherwise each word's casing learned from them per context (first/middle/last, all-caps line, after `: . ; ? ! -`), simple rules for unknown words | frozen 1.0; fresh 88.8% right with unmutated fresh words (simulated), just under the floor | **0.0** | fresh sample with mutated words: 1,828/5,000 | `jobs/2026-11-20__16-45-53` |

**Why the fresh sample is needed.** After pushing, `tests/data/answers.txt` is public in the
class repo, so a program can carry it as a lookup table (probe-lookup scored 100% on the
frozen exam). On every run, `tests/checks/fresh.py` makes 5,000 new titles with a random
seed from `os.urandom`. It builds them from words and spaces of the pool, so they contain
the same weird families, and none is equal to a pool title. About half of the words are
mutated (letters replaced, cases flipped, two words glued with `-`, `/` or `'`), so 46% of
fresh words appear nowhere in the public pool. I added this after probe-wordtable: with
unmutated words, a word table learned from the public answers was right on 88.8% of fresh
titles, which is too close to the 90% floor. With mutation it drops to 37.9%. Their answers come from the
original titlecase (`tests/original/`), run WITH `regex` in two processes with different
hash seeds, and only stable answers are kept. `behaviour` = **min**(frozen curve, fresh
curve). The verifier pins `regex==2026.11.19`, and I checked that Python 3.12 + that
version reproduces all 100,000 frozen answers byte for byte. My oracle got 0 of
100,000 wrong on 20 mutated fresh samples made locally, so this check does not make the
real port flaky. The rules gate also accepts Neha's and Yash's real ports (checked
locally), so it rejects cheats without rejecting honest solutions.

The probe-python hole was real in the old task. The old `no_python` check only searched
the source for `"os/exec"`, and the verifier image has `/usr/bin/python3`. The new
`tests/checks/rules.py` uses `go list -deps -json` to forbid importing `os/exec`, `syscall`,
`unsafe`, `plugin`, `C` and `runtime/cgo`, and any package outside the standard library.
It also forbids the names `StartProcess`, `ForkExec` and `go:linkname` in the source,
non-Go source files (assembly, C, `.syso`) and symbolic links. `instruction.md` states
all of these rules, so an honest agent knows them.
`rules.py` also rejects any package whose dependency tree contains `os/exec`, `plugin` or
`runtime/cgo`, which is what stops probe-cgi.
(One earlier probe-answers run, `jobs/2026-11-20__15-17-29`, failed before grading: a DNS
error while pulling `ghcr.io/astral-sh/uv`. It was re-run.)

## Exam: before and after

Old exam: 2,000 hidden titles (`tests/gen.py`, seed 1).
New exam: **100,000 titles, mode: regex** (titlecase WITH the `regex` package, stated in
`instruction.md`).

How the new exam was built (in a Linux `python:3.14-slim` container, because on Windows
the kit's `open(..., "w")` writes CRLF):
```
python -I kit/make_pool.py 100000 1 pool.txt          # twice: identical files
pip install regex                                     # regex 2026.11.19
python -I kit/answers.py task/environment/python-titlecase pool.txt key
```
`kit/report.txt`: pool 100000, kept 100000, **dropped 0**, `regex module used True`.
`key/inputs.txt` and `key/answers.txt` are copied to `task/tests/data/` (same md5).
Word families I added to `kit/make_pool.py` (marked "Added by Satyam Pandey") — neither
the trainer pool nor my old exam had them: `İstanbul`, `ﬁnance`, `ǅungla`, combining
accent `é`, `nasa’s`/`o’neil` (curly quote), `٣rd`, emoji, `½price`, `x²`, `Ⅰ`, `ẞTRASSE`,
`ß`, `mcé`, `dr.who`, `St.`; rarer whitespace (em space, narrow NBSP, ideographic space,
`\v`, `\f`, U+2028, U+1680); leading or trailing whitespace on the line.

Measured with `kit/compare.py key got.txt 2000` (files in `measure/`). The old-exam column
comes from `kit/old_exam.py measure/old-exam <got-old.txt>` (`measure/old-exam.txt`).
Each port reads one title per line on stdin, so no wrapper was needed.

| Port | Wrong on new exam | Old exam caught it? | Chance 2K random misses it | Reward on new exam |
|---|---|---|---|---|
| my oracle (before fix) | 1,499 | **no** (0 / 2,000 wrong) | 0% | 0.85 |
| my oracle (after fix) | **0** | n/a | n/a | 1.0 |
| Neha Gaur | 450 | yes (21 / 2,000 wrong) | 0% | 0.955 |
| Yash Singla | 3,231 | yes (67 / 2,000 wrong) | 0% | 0.68 |

Mode check: I also froze a no-`regex` answer key from the same pool (scratch only). All
three ports are closer to the regex mode (no-regex key: my old oracle 4,509, Neha 3,488,
Yash 6,188 wrong), so grading them in regex mode is fair.

### The new exam found a real bug in my own oracle

My port scored 1.0 on my old exam, but it was wrong on 1,499 of the 100,000 new titles.
Every one of the 1,499 had the same cause. Python's `str.upper()/lower()/capitalize()`
use full Unicode case mapping (`ß`→`SS`, `ﬁ`→`FI`, `ẞ`→`ß`, `İ`.lower()→`i̇`, final sigma
`Σ`→`ς`, and title case for the first letter in `capitalize`). My port used Go's 1:1
`unicode.ToUpper/ToLower`. Fix in `solution/solve.sh`:
- `casing.go`: `pyUpper`, `pyLower` (with Final_Sigma), `pyCapitalize`.
- `casetables.go`: generated by comparing Python 3.14's mapping with Go 1.23's for every
  code point. It lists only the differences (129 upper, 28 lower, 75 title).
  This was checked against Python for all 1.1M code points, including sigma contexts.

I did not remove any inputs. To check the fix goes beyond the pool, I ran a differential
fuzz: 2 × 200,000 random titles made of the hardest characters, original vs port. It
found two more gaps, both now fixed:
- the `regex` module's `\w` also counts `Nl` (`Ⅰ`), `Pc` (`‿`), Other_Alphabetic (`Ⓐ`)
  and Join_Control (ZWJ), which changes where `\b` falls;
- `regex.I` matches `ſ`≡`s`, `K` (Kelvin sign)≡`k` and `İ`≡`i` (affects small words,
  `Mr/Dr`, `[dol]`, `['s]` and consonant-only words).
After the fixes: **0 / 100,000 on the exam, 0 / 200,000 on each fuzz seed**. An exhaustive
check of `\w`, `\s`, `\p{Letter}` and `\p{Lu}` against the `regex` module also matches
for every character up to Unicode 15.

Known limit (honest): Go 1.23 knows Unicode 15, while Python 3.14 and `regex` 2026 know
Unicode 16/17. So letters added after Unicode 15 (for example the Garay script) can
still differ. The exam contains none of them.

Other fixes made along the way:
- The oracle's last line `go build ./...` failed because of the emptied `titlecase/` folder
  (Go writes the binary as `./titlecase`). `solve.sh` exited non-zero, although the Go
  files were already written. It now deletes empty folders and uses
  `go build -o /dev/null ./...`.
- `.gitattributes`: `*.sh`, `*.py`, `*.toml` and `Dockerfile` are always LF, and
  `task/tests/data/*.txt` is `-text`. A Windows checkout can then never add `\r` to the
  exam, and `behaviour.py` also strips CRLF defensively.

## Files changed
`task/instruction.md` (mode, rules, scoring), `task/task.toml` (version 1.1.0),
`task/tests/` (checks moved to `tests/checks/`, new `rules.py`, `fresh.py`, `test.sh`,
100k data, `tests/original/` = the original `titlecase/__init__.py` for fresh answers,
`regex` pinned in `tests/Dockerfile`; `gen.py` and the old 2,000-line files removed), `task/solution/solve.sh`,
`task/NOTES.md`, `kit/`, `measure/`, `harden-probes/`, `harden-results/`, `.gitattributes`.

## What I learned (3 lines)
1. My exam was too polite: my port was "perfect" on 2,000 titles and wrong on 1.5% of a weirder 100,000, all because of one missing idea (full Unicode case mapping).
2. A check that gives points on its own (`build`, `no_python`) is free points for a cheat. Rules belong in a gate, and only correct output earns points.
3. Grading untrusted code means sandboxing it: the answers must be unreadable while it runs, and "no Python" has to be enforced as "cannot start any program", not as a grep for `os/exec`.

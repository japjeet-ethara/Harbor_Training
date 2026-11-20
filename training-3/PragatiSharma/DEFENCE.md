# DEFENCE: titlecase-go (Day 6, Pragati Sharma)

The task is `training-3/PragatiSharma/task/`, verified at commit
`6e7932190e54f2cc454a858326f8ca62650cbb84` ("harden: close cheats 1-3, 100k exam (re)"). The
task folder is identical at the current HEAD and in the working tree. Details of every change
are in `HARDEN.md`; the measurements are in `measure/README.md`.

## Day 4: the strongest cheat

Ayush Khurana attacked this task (`../AyushKhurana/attack/ATTACK.md`, target commit
`8b79bbcfbcce50f0a50058fdf397cd55f0abc018`). His strongest cheat was **Cheat 2, "Python
inside"**:
- It renamed the original `titlecase/__init__.py` to `original_rules.txt`, so no `.py` file
  was left.
- A 40-line Go `main` then ran that code with `python3` at grading time.

**Original score: reward 1.000** (build 1, no_python 1, behaviour 1.0, 2,000/2,000).
- Ayush's run: job `jobs/2026-11-18__09-47-48` on his machine.
- I reproduced it before hardening: reward 1.0, job
  `training-3/PragatiSharma/jobs/2026-11-19__17-19-22`.
- Cheat 3, "read the exam", also scored 1.000, through a separate hole.

Day 4 scores under the original grader, `reward = (build + no_python + 4 × behaviour) / 6`:

| Cheat | Ayush's reward | My reproduction |
| --- | --- | --- |
| 1: lookup table of practice answers, echo the rest, delete `.py` | 0.364 | 0.364 |
| 2: Go wrapper runs the original Python (strongest) | 1.000 | 1.0 |
| 3: read `/tests/data/hidden_*` at run time | 1.000 | 1.0 |

## Vulnerabilities discovered

1. **Free credit for doing nothing useful.** `build` and `no_python` were worth 2/6 of the
   reward on their own. Deleting the `.py` files and echoing input scored 0.364 (Cheat 1).
2. **`no_python` checked file names only, and the program could run Python.** The verifier
   image ships `python3`, and the program ran as root with the grader's `PATH`, so renamed
   Python source passed (Cheat 2).
3. **The hidden answers were readable by the program under test.** It ran as root in the
   verifier, with `/tests` readable and its working directory in the workspace (Cheat 3).
4. **Found while hardening (not used by Ayush):**
   - the program could write the reward files in `/logs/verifier`;
   - processes it started could keep running after it exited;
   - the verifier had open network access (an HTTPS fetch succeeded).
5. **Found by the 100,000-input exam: the reference solution itself was wrong.** The
   original oracle failed 3,063 of 100,000 titles on Unicode case mapping (see "Surprise"
   below). Four more Python/Go differences existed that this exam did not trigger:
   - dotless `ı` under `re.IGNORECASE`;
   - long `ſ` under `re.IGNORECASE`;
   - U+001C to U+001F as whitespace;
   - Unicode 16.0 letters as word characters.

## Fixes made during Day 5

Round 1, on the 2,000-input exam (commit `cfa7980`):

| Fix | Closes |
| --- | --- |
| `build` and `no_python` became required conditions with weight 0; reward = behaviour | Cheat 1's free 2/6 |
| The program runs as UID 40000 (`setpriv`, no groups, no new privileges, `PATH=/usr/bin:/bin`), from a temporary folder holding only the binary | Cheats 2 and 3 |
| `/tests` and the Python interpreter are root-only, and the verifier image fails to build if UID 40000 can run Python or read the answers | Cheats 2 and 3 |
| `/logs/verifier` is mode 700, and every UID 40000 process is killed after the run | reward tampering, leftover processes |
| Verifier `network_mode = "no-network"` | HTTPS from the program (DNS still works) |

Round 2, the 100,000-input exam (commit `6e79321`):
- **New graded exam:** `task/tests/data/inputs.txt` and `answers.txt`, 100,000 titles.
  `kit/make_pool.py` generated them with eight new word families, and `kit/answers.py` froze
  them twice from the pinned original in `re` mode, with 0 dropped.
- **Practice pair:** renamed together to `practice_*`, otherwise unchanged.
- **Round-1 exam:** kept unchanged in `kit/evidence/old-exam-2000/`.
- **Grader:** it reads the new files and requires exactly 100,000 inputs and 100,000
  answers.
- **Answer-lock self-check:** the image build's check now targets `answers.txt`, after first
  confirming that file exists.
- **Generator:** `tests/gen.py` can no longer overwrite the exam.
- **Reference solution corrected:** Python's full case mappings, `\w`, `\s` and
  `re.IGNORECASE` folding, from tables generated with Python 3.14.2 and checked for every
  Unicode code point. It is still standard-library Go only.

## Before/after exam comparison

| | Before: round-1 exam | After: round-2 exam |
| --- | --- | --- |
| Graded titles | 2,000 (`hidden_inputs.txt`) | 100,000 (`inputs.txt`) |
| Answers SHA-256 | `4dcc8d7b9f0a866f…` | `e583966925128443…` |
| Titles already correct (echo score) | 92 (0.046) | 2,045 (0.02045) |
| Titles with case-expanding characters (`ﬁ`, `İ`, `ß`) | 0 | 8,765 |
| Titles with a typographic apostrophe `’` | 0 | 8,160 |
| Titles with other Unicode spaces | 0 | 7,814 |
| Original oracle (mine) | 2,000 / 2,000 | **96,937 / 100,000** |
| Ayush Khurana's port | 2,000 / 2,000 | 100,000 / 100,000 |
| Priyanshu Singh's port | 2,000 / 2,000 | 100,000 / 100,000 |
| Corrected oracle | 2,000 / 2,000 | 100,000 / 100,000 |

The trainer's `compare.py` gave a 0% chance that a random 2,000-title suite would catch any
of the 3,063 failures. `measure/README.md` has the commits, commands and runtimes.

Ayush's cheats across the three stages:

| Cheat | Original grader (round-1 exam) | Hardened grader, round-1 exam | Hardened grader, round-2 exam (Day 6) |
| --- | --- | --- | --- |
| 1 | 0.364 | 0.046 | 0.0205 |
| 2 | 1.0 | 0.0 | 0.0 |
| 3 | 1.0 | 0.046 | 0.0204 |

## Final Day 6 scores

Fresh Harbor 0.25.0 runs on 2026-11-20, on Windows with Docker Desktop:
- Each run used a disposable copy of `task/`, with only `solution/solve.sh` replaced by the
  script named below, byte-copied from the repository.
- The copies and jobs are under the git-ignored `jobs/` folder.
- `proof/` holds a byte copy of each trial's `verifier/reward.json`.
- Every Harbor command exited 0, with no exceptions and no errored trials.

| Run | Script | build | no_python | behaviour | reward | Expected | Proof |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Oracle | `task/solution/solve.sh` | 1.0 | 1.0 | 1.0 (100000/100000) | **1.0** | 1.0, met | `proof/oracle-reward.json` |
| Nop | Harbor `-a nop` | 0.0 | 0.0 | 0.0 (build condition failed) | **0.0** | 0.0, met | `proof/nop-reward.json` |
| Ayush Cheat 1 | `../AyushKhurana/attack/cheat1/solve.sh` | 1.0 | 1.0 | 0.0205 (2046/100000) | **0.0205** | < 0.2, met | `proof/ayush-cheat1-reward.json` |
| Ayush Cheat 2 | `../AyushKhurana/attack/cheat2/solve.sh` | 1.0 | 1.0 | 0.0 (0 lines, exit 1, `no python found`) | **0.0** | < 0.2, met | `proof/ayush-cheat2-reward.json` |
| Ayush Cheat 3 | `../AyushKhurana/attack/cheat3/solve.sh` | 1.0 | 1.0 | 0.0204 (2045/100000) | **0.0204** | < 0.2, met | `proof/ayush-cheat3-reward.json` |
| Task cheat | `task/cheat/solve.sh` | 1.0 | 0.0 | 0.0 (`no_python` condition failed: 3 `.py` files) | **0.0** | 0.0, met | `proof/task-cheat-reward.json` |

`reward.json` rounds to four decimals: Cheat 1 is exactly 0.02046, and Cheat 3 0.02045.
- **Cheat 3** searches for answer files named `inputs`/`answers`, which are the exam's real
  names. It scored exactly the echo score, so it could not read them.
- **Cheat 1** gets one title more than the echo score: `dr`, the only practice title in the
  exam.

### Job folder for every final run

Local and git-ignored (not committed), under `training-3/PragatiSharma/`:

| Run | Job folder | Trial |
| --- | --- | --- |
| Oracle | `jobs/2026-11-20__15-03-58` | `task__mShpFjg` |
| Nop | `jobs/2026-11-20__15-05-08` | `task__z6nhvhj` |
| Ayush Cheat 1 | `jobs/2026-11-20__15-05-56` | `task__BkjFQLN` |
| Ayush Cheat 2 | `jobs/2026-11-20__15-07-00` | `task__D9TEi9w` |
| Ayush Cheat 3 | `jobs/2026-11-20__15-08-07` | `task__KXBouNQ` |
| Task cheat | `jobs/2026-11-20__15-09-04` | `task__PdFRN7h` |

## Surprise

The biggest bug the 100,000-input exam found was in my own reference solution, not in a
cheat. My oracle scored 2,000/2,000 on the round-1 exam and Harbor gave it 1.0, yet it
failed 3,063 of the 100,000 new titles. Both classmates' ports scored 100,000.

The cause was Go's `strings.ToUpper` and `strings.ToLower`, which map one character to one:
- Python turns `ﬁnal` into `FInal`; my port left `ﬁnal`.
- Python lowercases `İ` to `i` plus a combining dot; my port gave a plain `i`.

The round-1 exam had none of these characters, so it could not see the bug. A larger,
deliberately varied exam tests the answer key's author as much as the agents. (The remaining
limitations, such as memorising the public answers, are listed in `HARDEN.md`.)

# HARDEN: titlecase-go (Day 5)

Two hardening rounds:

- **Round 1 (2,000 inputs)** closed three cheats. Its sections below are kept as measured.
- **Round 2 (100,000 inputs)** replaced the graded exam, corrected the reference port, and
  reran every attack. It starts at [Round 2](#round-2-100000-input-exam).

## Version

- Attack target (Ayush Khurana, `attack/TARGET.txt`): `PragatiSharma/titlecase-go` @
  `8b79bbcfbcce50f0a50058fdf397cd55f0abc018`.
- Tested: `training-3/PragatiSharma/task` @ `ae96885bdbcab8a6726074e08e2acfc80842d60f`.
- All 38 files are byte-identical. The only difference is git file mode 100755 → 100644
  on `cheat/solve.sh`, `solution/solve.sh` and `tests/test.sh`.

## Datasets (round 1, 2,000 inputs)

As the SOP requires, the generated inputs and answers are committed in `task/tests/data/`.
They were last changed in commit `6504b045a6c358671884ca981b6862e0cc9f0031` and were not
changed in this round.

| File | Records | SHA-256 |
| --- | --- | --- |
| `hidden_inputs.txt` | 2,000 | `017c6ffc7992c0df12185961d24d4ca6266432eebb406c18bcf25e941664e852` |
| `hidden_expected.txt` | 2,000 | `4dcc8d7b9f0a866fb209de6ba171be07dfe30030d595959315cf1118af1daf9a` |
| `inputs.txt` (practice) | 2,000 | `2f086c791fa087200506e0a6eba7dd58517884d5b98ac63dc07e89e62f269052` |
| `expected.txt` (practice) | 2,000 | `04afbf845881398322c49da41c8ca658436a5c337ef96a69356d8df3b90232f2` |

No hidden input appears in the practice set. 92 hidden titles are already titlecased,
so a program that echoes its input scores 92 / 2,000 = 0.046.

## Method

For each run: a fresh copy of the task, with only `solution/solve.sh` replaced, then
`harbor run -p <copy> -a oracle` (or `-a nop`) with Harbor 0.25.0 on Windows with Docker
Desktop. Scores are read from each trial's `verifier/reward.json`. All job folders are
local; none are committed.

## Before hardening

Original grader: `reward = (build + no_python + 4 × behaviour) / 6`.

| Cheat | build | no_python | behaviour | reward | Ayush reported | Job folder (local) |
| --- | --- | --- | --- | --- | --- | --- |
| 1: lookup table of practice answers, echoes the rest, deletes `.py` | 1.0 | 1.0 | 0.046 | 0.364 | 0.364 (match) | `C:\Users\PragatiSharma\Documents\harbor-work\day5-tests\jobs\2026-11-19__17-29-58` |
| 2: Go wrapper runs the original Python (renamed `original_rules.txt`) through `python3` | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 (match) | `C:\Users\PragatiSharma\Documents\harbor-work\Harbor_Training\training-3\PragatiSharma\jobs\2026-11-19__17-19-22` (git-ignored) |
| 3: reads `/tests/data/hidden_*` at run time | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 (match) | `C:\Users\PragatiSharma\Documents\harbor-work\day5-tests\jobs\2026-11-19__17-31-25` |

A first Cheat 1 attempt, run from a longer folder path, stopped before grading with a
Windows path-length error (`FileNotFoundError`, 260-character path). It produced no score
and was rerun from the shorter path shown above.

## Fixes

1. **Required conditions** (`tests/grade/reward.toml`, `tests/grade/behaviour/check.py`).
   Behaviour is 0 unless `go build ./...` succeeds and no `.py` file remains. The reward is
   the behaviour score; `build` and `no_python` carry weight 0 but are still reported.
   This closes Cheat 1's free 2/6.
2. **No Python for the submitted program** (`tests/grade/support.py`, `tests/Dockerfile`).
   The program runs as the unprivileged UID 40000 (`setpriv`, no groups, no new
   privileges, `PATH=/usr/bin:/bin`). `/usr/local/bin/python3.12`, `libpython3*` and
   `/usr/local/lib/python3.12` are root-only. Every interpreter path Cheat 2 tries is
   refused (`python3`, `python` and `/usr/local/bin/python3` resolve to `python3.12`;
   `/usr/bin/python3` and `/usr/bin/python` do not exist). The grader, running as root,
   is unaffected. The verifier image fails to build if UID 40000 can still run Python.
3. **Hidden answers locked** (`tests/Dockerfile`). `/tests` is root-only. The program's
   working directory is a temporary directory containing the built binary, not the
   workspace. This closes Cheat 3. The verifier image fails to build if UID 40000 can
   read the hidden answers.
4. **Reward files protected** (`tests/test.sh`, `tests/grade/support.py`).
   `/logs/verifier` is set to mode 700 before grading. After the program runs, every
   UID 40000 process is killed, so nothing it started can rewrite `reward.json`.
5. **Verifier network restricted** (`task.toml`). `[verifier] network_mode = "no-network"`.
   The measured effect is in "Network measurements" below.

## After hardening (round 1, 2,000 inputs)

Measured on `day5-tests\fix1\candidate-v2`. The seven changed files in `task/` were copied
from it and verified byte-identical, so the task folder now matches it exactly.

| Run | build | no_python | behaviour | reward | Job folder (local) |
| --- | --- | --- | --- | --- | --- |
| Oracle (`solution/solve.sh`) | 1.0 | 1.0 | 1.0 (2000/2000) | **1.0** | `C:\Users\PragatiSharma\Documents\harbor-work\day5-tests\fix1\jobs\2026-11-19__18-05-34` |
| Cheat 1 | 1.0 | 1.0 | 0.046 (92/2000) | **0.046** | `C:\Users\PragatiSharma\Documents\harbor-work\day5-tests\fix1\jobs\2026-11-19__18-06-40` |
| Cheat 2 | 1.0 | 1.0 | 0.0 (exit 1, `no python found`) | **0.0** | `C:\Users\PragatiSharma\Documents\harbor-work\day5-tests\fix1\jobs\2026-11-19__18-07-40` |
| Cheat 3 | 1.0 | 1.0 | 0.046 (92/2000) | **0.046** | `C:\Users\PragatiSharma\Documents\harbor-work\day5-tests\fix1\jobs\2026-11-19__18-08-41` |
| Nop | 0.0 | 0.0 | 0.0 (failed build condition) | **0.0** | `C:\Users\PragatiSharma\Documents\harbor-work\day5-tests\fix1\jobs\2026-11-19__18-09-40` |
| Task cheat (`cheat/solve.sh`) | 1.0 | 0.0 | 0.0 (failed `no_python` condition, 3 `.py` files) | **0.0** | `C:\Users\PragatiSharma\Documents\harbor-work\day5-tests\fix1\jobs\2026-11-19__18-10-30` |

Targets: oracle 1.0, every cheat below 0.2. All met.

The intermediate candidate (the same grader without the `task.toml` network setting) gave
the same rewards: oracle 1.0, Cheat 1 0.046, Cheat 2 0.0, Cheat 3 0.046, nop 0.0 and task
cheat 0.0. Jobs: `...\day5-tests\fix1\jobs\2026-11-19__17-45-35`, `__17-46-29`,
`__17-47-22`, `__17-48-17`, `__18-01-10` and `__18-01-58`.

## Network measurements

A test-only probe program (`day5-tests\fix1\probe\solve.sh`, not committed) ran as the
submitted program. It sends no user or project data.

| Probe | Before: verifier `public` | After: verifier `no-network` |
| --- | --- | --- |
| Program UID | 40000 | 40000 |
| DNS lookup of `example.com` | succeeded | **succeeded** |
| TCP connect to `1.1.1.1:443` | succeeded | succeeded (connect only) |
| HTTPS GET `https://example.com/` | succeeded | **failed** (`EOF`) |
| HTTPS GET `https://raw.githubusercontent.com/` | succeeded | **failed** (`EOF`) |
| Agent phase: `curl https://example.com` | HTTP 200 | HTTP 200 (agent network unchanged) |
| Job | `...\day5-tests\fix1\jobs\2026-11-19__18-02-50` | `...\day5-tests\fix1\jobs\2026-11-19__18-04-22` |

How Harbor 0.25.0 enforces `no-network` on local Docker (read from its source, not
measured): all TCP from the container is redirected to a proxy with an empty allowlist,
so a TCP connect succeeds locally and is then closed. DNS to the container's configured
nameserver is allowed. ICMP is allowed. Other non-TCP traffic is rejected. Not measured:
plain HTTP on port 80, other TCP ports, ICMP, and non-DNS UDP. If a backend cannot enforce
`no-network`, Harbor rejects the task rather than running it with the network open.

## Round 2: 100,000-input exam

Prepared and measured on a candidate outside the repository, built from
`training-3/PragatiSharma/task` @ `cfa79805bd953a91f385b1b749c36ae8e0e38db9` (the round-1
hardened task).

### Dataset changes

| Before (round 1) | After (round 2) | SHA-256 |
| --- | --- | --- |
| `tests/data/inputs.txt` (practice) | `tests/data/practice_inputs.txt` (renamed with its pair, bytes unchanged) | `2f086c791fa087200506e0a6eba7dd58517884d5b98ac63dc07e89e62f269052` |
| `tests/data/expected.txt` (practice) | `tests/data/practice_expected.txt` (renamed with its pair, bytes unchanged) | `04afbf845881398322c49da41c8ca658436a5c337ef96a69356d8df3b90232f2` |
| — | `tests/data/inputs.txt`: graded exam, 100,000 records | `779b81d3930a23b0f3af5cf56ef19de29dea3cb632e6aca1fce2a5e20da9606f` |
| — | `tests/data/answers.txt`: graded answers, 100,000 records | `e583966925128443d0fc96d605bed9b486c72463e14b79f66a1add0343ac1b36` |
| `tests/data/hidden_inputs.txt` (graded) | `kit/evidence/old-exam-2000/hidden_inputs.txt` (not graded, bytes unchanged) | `017c6ffc7992c0df12185961d24d4ca6266432eebb406c18bcf25e941664e852` |
| `tests/data/hidden_expected.txt` (graded) | `kit/evidence/old-exam-2000/hidden_expected.txt` (not graded, bytes unchanged) | `4dcc8d7b9f0a866fb209de6ba171be07dfe30030d595959315cf1118af1daf9a` |

- **How the exam was built:** `kit/make_pool.py` generated it (100,000, seed 1, with added
  word families), and `kit/answers.py` froze it twice from the pinned original in `re` mode.
  Both freezes kept 100,000 and dropped 0, and they are byte-identical. `kit/NOTES.md` has
  the commands, the checks and the `-I`/`PYTHONHASHSEED` behaviour.
- **Echo floor:** 2,045 answers equal their input, so echoing scores 0.02045.
- **Practice overlap:** one exam title (`dr`) is also a practice title.

### Grader and task changes

1. **Exam paths and counts** (`tests/grade/behaviour/check.py`, `tests/grade/support.py`).
   - Behaviour now reads `/tests/data/inputs.txt` and `/tests/data/answers.txt`.
   - `HIDDEN_RECORD_COUNT = 2000` becomes `EXAM_RECORD_COUNT = 100000`.
   - Behaviour scores 0 unless both files hold exactly 100,000 records; before, only the
     answer count was checked.
2. **Answer-access proof** (`tests/Dockerfile`). It now targets `data/answers.txt`. A
   root-side `test -s` comes first, so the check cannot pass just because the file is
   missing.
3. **Generator** (`tests/gen.py`).
   - It writes only the practice pair and refuses the exam file names.
   - It takes an optional path to the original, because the old default path does not
     exist in this layout.
   - Rerun with the pinned original, it rewrote both practice files byte-identically and
     left `inputs.txt` and `answers.txt` untouched.
   - The same generator reproduces the retained round-1 exam exactly
     (`kit/tools/check_round1_evidence.py`).
4. **Reference solution** (`solution/solve.sh`, SHA-256
   `8546e114cf5e717f09f07d94c64ed31123edfb343fcc6d18316fc768fa69c0e8`). It is corrected; see
   below.
5. **Unchanged:** every round-1 protection:
   - required conditions;
   - UID 40000 with `setpriv`;
   - `PATH=/usr/bin:/bin`;
   - the kill sweep;
   - root-only `/tests` and Python, with the build-time self-check;
   - `/logs/verifier` at mode 700;
   - verifier `no-network`.

   `RUN_TIMEOUT_SEC` stays 60. The corrected oracle needs about 2 s for 100,000 titles.

### Three-port comparison (baseline, before any fix)

From `measure/README.md`, which also has the source commits, commands, runtimes and evidence.
The ports are the task oracle as committed (`6504b045`), Ayush Khurana's (`9234582e`) and
Priyanshu Singh's (`30cf18a1`). Scoring used the trainer's `kit/compare.py`.

| Port | Round-1 exam (2,000) | 100,000 exam |
| --- | --- | --- |
| Task oracle (original) | 2,000 correct | 96,937 correct, **3,063 wrong** |
| Ayush Khurana | 2,000 correct | 100,000 correct |
| Priyanshu Singh | 2,000 correct | 100,000 correct |

All six runs exited 0 and printed one line per input. The original oracle's failures were:
- 2,653 titles with the `ﬁ`/`ﬂ` ligatures, where Python's `upper()` gives `FI`/`FL`;
- 410 titles with `İ` in all-caps text, where Python's `lower()` gives `i` + U+0307.

Go's `strings.ToUpper` and `strings.ToLower` only do one-to-one mappings.

### Corrected oracle (separate result)

The corrected port computes:
- Python's full case mappings (`upper`, `lower` with Final_Sigma, `capitalize`);
- `\w` and `\s`;
- `re.IGNORECASE` folding.

Its tables are generated from Python 3.14.2 (Unicode 16.0.0) and checked for all 1,112,064
code points. It is still standard-library Go with no Python at run time. The generators, the
tests and the 74 regression titles are in `measure/oracle/`.

| Version | Round-1 exam | 100,000 exam | Practice | Regression titles |
| --- | --- | --- | --- | --- |
| Original | 2,000 / 2,000 | 96,937 / 100,000 | 2,000 / 2,000 | 22 / 74 |
| Fix 1 (case mappings) | 2,000 / 2,000 | 100,000 / 100,000 | 2,000 / 2,000 | 61 / 74 |
| Fix 2 (final; adds `\w`, `\s`, IGNORECASE) | **2,000 / 2,000** | **100,000 / 100,000** | **2,000 / 2,000** | **74 / 74** |

### Harbor results (round 2, 100,000 inputs)

Each run used a fresh copy of the candidate task, with only `solution/solve.sh` replaced, and
was run with Harbor 0.25.0 on Windows with Docker Desktop. Scores come from each trial's
`verifier/reward.json`; the exact match counts come from `verifier/test-stdout.txt`. Copies of
the reward files are in `measure/harbor/`.

| Run | build | no_python | behaviour | reward | Target | Job folder (local) |
| --- | --- | --- | --- | --- | --- | --- |
| Corrected oracle (`solution/solve.sh`) | 1.0 | 1.0 | 1.0 (100000/100000) | **1.0** | 1.0, met | `C:\Users\PragatiSharma\Documents\harbor-work\day5-tests\exam100k\hv\jobs\2026-11-19__22-14-21` |
| Nop | 0.0 | 0.0 | 0.0 (failed build condition) | **0.0** | 0.0, met | `C:\Users\PragatiSharma\Documents\harbor-work\day5-tests\exam100k\hv\jobs\2026-11-19__22-15-40` |
| Cheat 1 (Ayush, unchanged) | 1.0 | 1.0 | 0.0205 (2046/100000) | **0.0205** | < 0.2, met | `C:\Users\PragatiSharma\Documents\harbor-work\day5-tests\exam100k\hv\jobs\2026-11-19__22-16-34` |
| Cheat 2 (Ayush, unchanged) | 1.0 | 1.0 | 0.0 (0 records, exit 1, `no python found`) | **0.0** | < 0.2, met | `C:\Users\PragatiSharma\Documents\harbor-work\day5-tests\exam100k\hv\jobs\2026-11-19__22-17-43` |
| Cheat 3 (Ayush, unchanged) | 1.0 | 1.0 | 0.0204 (2045/100000) | **0.0204** | < 0.2, met | `C:\Users\PragatiSharma\Documents\harbor-work\day5-tests\exam100k\hv\jobs\2026-11-19__22-18-51` |
| Task cheat (`cheat/solve.sh`) | 1.0 | 0.0 | 0.0 (failed `no_python` condition, 3 `.py` files) | **0.0** | 0.0, met | `C:\Users\PragatiSharma\Documents\harbor-work\day5-tests\exam100k\hv\jobs\2026-11-19__22-19-59` |

Harbor reported no exceptions and no errored trials, and every Harbor command exited 0.

- **Rounding:** `reward.json` rounds to four decimals. The exact Cheat 1 score is
  2046/100000 = 0.02046, and Cheat 3's is 2045/100000 = 0.02045.
- **Cheat 1** (practice lookup table plus echo) gains one title over the echo floor: `dr`,
  the only practice title in the exam.
- **Cheat 3** looks for `inputs`/`answers` file pairs, which are the new exam's own names. It
  scored exactly the echo floor, so it found no readable answers.
- **Verifier network:** the verifier logs also show rewardkit's LiteLLM failing to fetch a
  remote price list (`EOF`), which is consistent with the `no-network` setting. The fetch
  does not affect grading.

### Pending

- A confirmation run from the committed task folder, after the files are copied in.
- New screenshots for the hardened grader. The current screenshots in `task/screenshots/`
  are pre-hardening results.

## Remaining limitations

1. **Public-dataset memorisation.** As the SOP requires, the exam inputs and answers are
   committed, so they are public. A program can embed `answers.txt` as a lookup table
   (about 3.6 MB) and score 1.0 without network or file access at grading time. This was
   not run as a test; it follows from how behaviour is scored.
2. **Agent-phase network.** `[environment] network_mode = "public"` is unchanged; the probe
   measured HTTP 200 from the agent container. An agent could download the committed
   answers while it works.
3. **Partial verifier network block.** Under `no-network`, DNS lookups from the program
   still succeeded (measured). ICMP is allowed by Harbor's rules (not tested). A program
   could use either to exchange data with a server its author controls.
4. **Bundled interpreters.** Only the system Python is locked. A submission can still
   bring its own interpreter: a pure-Go Python interpreter vendored into the module (the
   "standard library only" rule is not checked by the grader), or a Python binary embedded
   in the Go program and run from `/tmp` or from memory. `no_python` checks only file
   names, so renamed Python source (as in Cheat 2) still passes it.
5. **Other interpreters.** `perl`, `sh` and `bash` remain usable by UID 40000. That is not
   Python, but a non-Go port would pass. `/bin/sh` is also used by the cleanup step.
6. **Partial credit.** Echoing the input scores 0.02045 on the round-2 exam (0.046 on round 1),
   and a partial port earns partial credit (by design).
7. **Assumptions.** The protections assume a Linux verifier running as root in a
   disposable container (Harbor's default here). `go build` runs as root; with cgo off and
   `GOTOOLCHAIN=local` it does not run submission code, but this was not separately tested.

# HARDEN: titlecase-go (Day 5, round 1: 2,000 inputs)

These results come from the **first hardening round**, run against the 2,000-input
datasets listed below. The 100,000-input exam and the three-port comparison are
**pending**.

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

## Pending

- The 100,000-input exam.
- The three-port comparison.
- A confirmation run from the committed task folder.
- New screenshots for the hardened grader. The current screenshots in `task/screenshots/`
  are pre-hardening results.

## Remaining limitations

1. **Public-dataset memorisation.** As the SOP requires, the hidden inputs and answers are
   committed, so they are public. A program can embed `hidden_expected.txt` as a lookup
   table and score 1.0 without network or file access at grading time. This was not run as
   a test; it follows from how behaviour is scored.
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
6. **Partial credit.** Echoing the input scores 0.046, and a partial port earns partial
   credit (by design).
7. **Assumptions.** The protections assume a Linux verifier running as root in a
   disposable container (Harbor's default here). `go build` runs as root; with cgo off and
   `GOTOOLCHAIN=local` it does not run submission code, but this was not separately tested.

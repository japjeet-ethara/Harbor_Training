# Attack Report — Shivam Tiwari → Mohsin Raza

## Target snapshot

- Target: Mohsin Raza — Titlecase Go
- Source path: `mohsin-raza-ethara/titlecase-go`
- Snapshot commit SHA: `3411444a747ca2f5642838d83a79a6d28aa17be0`
- Local scratch path: `training-3/ShivamTiwari/attack/target/`
- Target tests/task.toml/environment unchanged: yes

The scratch copy was verified byte-for-byte against the 18 files tracked at the
snapshot commit after all runs. `TARGET.txt` contains the one-line target and
SHA.

## Exam overview

- Agent workspace: `/workspace/repo` is a checkout of `python-titlecase`
  copied in by `environment/Dockerfile:10`; the agent must replace it with a Go
  program. `environment/Dockerfile:12` sets that path as the working directory.
- Verifier isolation: `task.toml:15` declares `environment_mode = "separate"`,
  and `task.toml:2` collects `/workspace/repo`. The verifier image is
  `tests/Dockerfile:1` (`golang:1.23`), and `tests/Dockerfile:12` copies the
  whole tests directory to `/tests/`, including the hidden fixtures.
- Checks and weights: `build` weight 1, `no_python` weight 1, `behaviour`
  weight 10 (`tests/checks.py:150-152`). `tests/reward.toml:7-8` and `:15`
  aggregate them with `weighted-mean`; `tests/reward.toml:5` still says
  behaviour has weight 4, which is stale.
- Reward aggregation: weighted mean over the three criteria, i.e.
  `(1*build + 1*no_python + 10*behaviour) / 12`.
- Visible fixtures: no answer fixture is shipped in the agent container. The
  only agent-visible answer-like data is the upstream library's
  `titlecase/tests.py:16` `TEST_DATA` table (73 pairs). Its inputs have zero
  exact overlap with the hidden inputs, so a pure visible-fixture lookup cannot
  score behaviour points.
- Hidden fixtures: `tests/data/hidden_inputs.txt` and
  `tests/data/hidden_expected.txt`, 2000 lines each. `tests/gen.py:298-306`
  seeds generation deterministically and asserts that the hidden input set is
  disjoint from the visible input set. They are bundled only into the verifier
  image by `tests/Dockerfile:12`.
- Behaviour scoring: `tests/checks.py:124-134` builds the agent's main package
  inside the verifier container and runs the resulting binary with
  `cwd=/workspace/repo`, feeding the hidden inputs on stdin.
  `tests/checks.py:139-145` compares stdout line by line and returns
  `matched / len(expected)`.

The separation is therefore only between the agent phase and the verifier
phase. During scoring, agent-produced code executes inside the same verifier
container whose `/tests/data/` directory contains the answers.

## Cheat 1 — Verifier-runtime hidden-answer replay

- What it does: replaces `solution/solve.sh` with a Go program that tries
  `/tests/data/hidden_expected.txt` (plus `/app/tests/data/...` and a relative
  path), falls back to walking `/tests` for `hidden_expected.txt`, and prints
  that file. If no answer file is found it echoes stdin unchanged. It also
  creates `go.mod` and deletes every `.py`/`.pyc`/`.pyo` file.
- Why this is not a full correct Go port: the program contains no titlecase
  logic at all. It only reads the verifier's answer file and replays it.
- Harbor score: `1.0`
- Component scores: `build = 1.0`, `no_python = 1.0`, `behaviour = 1.0`
- Job folder:
  `C:\Users\ShivamTiwari\attack\jobs-day4\day4-cheat1c`
  (trial `target__6EBSTdG`)
- Verifier artifact: `verifier/reward.json` → `{"reward": 1.0}`;
  `verifier/reward-details.json` shows all three criteria at 1.0, and
  `verifier/test-stdout.txt` ends with `reward: 1.0`.
- Evidence (target file:line):
  - `tests/test.sh:10-12` runs `rewardkit /tests` with
    `--workspace /workspace/repo` and writes `/logs/verifier/reward.json`.
  - `tests/Dockerfile:12` copies the hidden fixtures into `/tests/`.
  - `tests/checks.py:24` resolves the fixtures as `.../data` beside
    `checks.py`, i.e. `/tests/data`.
  - `tests/checks.py:126` builds the agent package inside the verifier;
    `tests/checks.py:130-134` runs the binary with the hidden inputs on stdin;
    `tests/checks.py:139-145` compares its stdout with the hidden expected
    file.
  - `task.toml:15` says the verifier is separate, but the binary is executed
    inside that separate verifier container, not in a sandbox that hides
    `/tests`.
- Why it scored this way: the agent-built binary could read
  `/tests/data/hidden_expected.txt` directly. The fallback in this cheat is an
  identity transform; the committed oracle baseline (below) produced 0.0
  behaviour with an answer table for the visible fixtures, so an identity or
  visible-only fallback cannot produce 2000/2000 matching lines. The 1.0
  behaviour result is therefore attributable to the hidden-answer read.
- Recommended fix: score the binary in a sanitised container that contains the
  binary and the input stream but not `/tests` or any expected-answer file; or
  stream inputs from the verifier and keep expected answers outside the
  process's filesystem and mount namespace. Run the scorer unprivileged and
  make `/tests` unreadable to it.

## Cheat 2 — Build-only structural shortcut

- What it does: creates a minimal `main.go` that compiles, discards stdin, and
  prints one fixed wrong line (`not implemented`). The script removes the
  Python sources and caches.
- Why this is not a full correct Go port: it implements none of the required
  titlecase behaviour.
- Harbor score: `0.1667`
- Component scores: `build = 1.0`, `no_python = 1.0`, `behaviour = 0.0`
- Job folder:
  `C:\Users\ShivamTiwari\attack\jobs-day4\day4-cheat2`
  (trial `target__f5tbBYo`)
- Verifier artifact: `verifier/reward.json` → `{"reward": 0.1667}`;
  `verifier/reward-details.json` shows the component values above.
- Evidence (target file:line):
  - `tests/checks.py:94-96` gives a full point for `go build ./...`.
  - `tests/checks.py:99-105` gives a second full point for having no `.py`
    files and a successful build.
  - `tests/checks.py:150-152` weights those two criteria 1 each against
    behaviour's 10, so `(1+1)/12 = 0.1667`.
- Why it scored this way: `build` and `no_python` are independent of behaviour
  and have no minimum-correctness gate. A program that never titlecases still
  collects both.
- Recommended fix: require a minimum behaviour score before awarding the
  structural points, or fold structural checks into a single gate that only
  pays out once behaviour is non-trivial.

## Cheat 3 — Weak partial Titlecase port

- What it does: a real but deliberately incomplete Go implementation. It
  splits input on line breaks, preserves whitespace, lowercases a small-word
  list, capitalises the first letter of other words, lowercases the rest, and
  capitalises a small word at the start or end of a line.
- Why this is not a full correct Go port: it omits the Mc/Mac rules
  (`python-titlecase/titlecase/__init__.py:133-137`), titles
  (`:139-143`), apostrophe-second words (`:125-131`), inline periods and
  upper-case words elsewhere (`:145-147`), slash and hyphen recursion
  (`:152-166`), consonant-only acronyms (`:172-180`), the all-caps path
  (`:120-123`), and sub-phrase capitalisation (`:205-208`). It also does not
  special-case punctuation before a word.
- Harbor score: `0.5133`
- Component scores: `build = 1.0`, `no_python = 1.0`,
  `behaviour = 0.416` (832 of 2000 hidden lines matched exactly)
- Job folder:
  `C:\Users\ShivamTiwari\attack\jobs-day4\day4-cheat3`
  (trial `target__AnGhoGH`)
- Verifier artifact: `verifier/reward.json` → `{"reward": 0.5133}`;
  `verifier/reward-details.json` shows `behaviour = 0.416`.
- Evidence (target file:line):
  - `tests/checks.py:139-145` pays per matching line, not per test case.
  - `tests/gen.py:86-194` deliberately includes the hard categories listed
    above in the generated fixtures.
  - `tests/checks.py:150-152` gives behaviour 10/12 of the total, so 41.6%
    line accuracy converts to 0.5133 overall.
- Why it scored this way: the simple sentences and the all-caps normal-word
  sentences are close enough to the reference for the naive transform, while
  the omitted categories fail. The partial-credit formula rewards that partial
  coverage heavily.
- Recommended fix: reduce or remove per-line partial credit for behaviour, for
  example require every line in a case to match, or use a threshold that a
  weak port cannot reach.

## Baseline — committed oracle is already a lookup cheat

This was not counted as one of the three cheats, but it is important evidence.

- The committed `solution/solve.sh` embeds the entire visible
  `tests/data/expected.txt` as a Go raw string (`solution/solve.sh:20`) and its
  `main` discards stdin and writes that constant
  (`solution/solve.sh:2022-2024`).
- `cheat/solve.sh` is byte-identical to `solution/solve.sh`.
- Harbor run of the unmodified committed solution:
  - Job folder:
    `C:\Users\ShivamTiwari\attack\jobs-day4\day4-original-oracle`
    (trial `target__bTy4s9e`)
  - Score: `0.1667`; components `build = 1.0`, `no_python = 1.0`,
    `behaviour = 0.0`
- This confirms two things: the visible-answer lookup strategy cannot score
  behaviour points against the disjoint hidden fixtures, and the task's own
  oracle does not reach full reward. `solution/solve.sh.real.bak` contains a
  real implementation and should replace it.

## Comparison

| Cheat | Strategy | Reward | Job folder | Main weakness tested |
|---|---|---:|---|---|
| 1 | Replay hidden answer file from verifier filesystem | 1.0000 | `day4-cheat1c` | Verifier executes agent binary beside hidden answers |
| 2 | Compile only; no behaviour | 0.1667 | `day4-cheat2` | Structural criteria pay without correctness |
| 3 | Weak partial titlecase port | 0.5133 | `day4-cheat3` | Per-line partial credit rewards incomplete behaviour |

## Strongest cheat

- Highest verified reward: `1.0` (Cheat 1)
- Why: the behaviour check runs the agent-built binary inside the verifier
  container, and the hidden expected answers are readable at
  `/tests/data/hidden_expected.txt`. The binary can replay them without
  implementing the task.
- Evidence: `tests/Dockerfile:12`, `tests/checks.py:24`,
  `tests/checks.py:126-134`, `tests/test.sh:10-12`, and the real run in
  `day4-cheat1c` with `behaviour = 1.0`.

## Recommendations for Mohsin

1. Run the behaviour binary in a separate, sanitised container that exposes
   only the binary and stdin; do not mount `/tests` or any expected-answer file
   into that container. Keep the expected answers in the orchestrator and
   compare them there.
2. Replace the committed `solution/solve.sh` with the real implementation
   already stored in `solution/solve.sh.real.bak`, delete the duplicate
   `cheat/` folder at the task root, and add an oracle regression that asserts
   reward `1.0`.
3. Remove or correct the stale `tests/reward.toml:5` comment (it says behaviour
   weight 4 while `tests/checks.py:152` registers 10), and consider a stronger
   behaviour weight or a correctness gate before paying structural points.
4. Make hidden inputs unpredictable per run, for example by generating them at
   verification time with a per-run secret seed, so a static answer file cannot
   be replayed even if it is reachable.
5. Reduce per-line partial credit or require an exact whole-output match for
   the behaviour criterion; a 41.6% line match currently earns 0.5133 overall.

## Run integrity

- All scores are from real Harbor runs: yes
- Any infrastructure failures: two early attempts (`day4-cheat1`,
  `day4-cheat1b`) failed before producing a reward and were not recorded as
  scores.
  - The task's `environment/docker-compose.yaml` expects the task directory to
    be named `titlecase-go` next to `python-titlecase`. A local junction was
    created so the unmodified compose file resolves.
  - The Windows checkout had `core.autocrlf=true`, which made
    `/tests/test.sh` unexecutable inside the verifier (`/bin/bash\r`). The
    scratch target and reference copy were rebuilt from the commit blobs with
    LF endings; their content still matches the snapshot commit byte-for-byte.
  - The local reference copy is at `attack/python-titlecase/`; it and the
    `attack/titlecase-go` junction are local scaffolding, not deliverables, and
    are ignored by Git.
- Any deviations from assignment:
  - Cheat 1 was adapted from the guide's "visible-answer lookup" candidate to
    verifier-runtime answer replay after establishing that the agent-visible
    library test table has zero overlap with the hidden fixtures. The
    visible-lookup candidate is covered by the baseline run above.
  - One baseline Harbor run of the committed oracle was added; it is reported
    separately and is not one of the three cheat deliverables.
  - Harbor job directories are outside the deliverable at
    `C:\Users\ShivamTiwari\attack\jobs-day4`.
- No Git commit, push, or pull request was made.

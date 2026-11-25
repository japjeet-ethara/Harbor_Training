# Attack Report - titlecase-go

## Target

- Task: `practice/titlecase-go`
- Target folder: `attack/target/`
- Target owner: Gunjit Arora
- Repository: `japjeet-ethara/Harbor_Training`
- Repository commit recorded in `TARGET.txt`: `65064f8daa60e919c35d71d891eeea7d78bcee9e`
- Task's upstream Python source commit in `target/task.toml`: `42f43e2de55bf003b286c6f8e8d8b2d26676a167`

The supplied reference about Utkarsh Gupta's task was used as a report-structure example only. Its task settings and vulnerabilities are not attributed to this target.

## Assessment and runtime boundaries

The task asks for a Go 1.23 program that titlecases newline-delimited UTF-8 input. The original task files were reviewed read-only, including the instructions, reference solution, generator, tests, task configuration, Dockerfiles and scoring.

This task declares a separate verifier in `target/task.toml`. The agent image copies the original Python project into `/workspace/repo`; the verifier image places tests at `/tests`, restricts access to root, removes system Python, and runs the submitted program as `nobody`. Therefore, repository presence of test or solution files does not by itself prove they are accessible to the submitted program. Runtime accessibility claims below are limited to what the actual collected artifacts and results establish.

The reward is a weighted mean: build weight 1, no-Python weight 1, behavior weight 4. A buildable program with no Python files can earn the two fixed-check points even if behavior is poor. In the first Cheat 2 run, behavior was 0.0135, producing reward 0.3423.

## Main assessment findings

1. **Reference implementation reuse (confirmed in a Harbor result).** The reference exists at `target/solution/port/`. The Cheat 1 trial's collected `main.go` had the same SHA-256 as that reference and the trial received full reward. Keep the oracle outside agent-accessible paths and use it only in a separate validation process.
2. **Fixed points for non-behavior checks.** `target/tests/checks/reward.toml:1-4` assigns build and no-Python one point each and behavior four points. The first Cheat 2 result demonstrates that a buildable echo can still receive 0.3423. Consider gating fixed-check credit on a minimum behavior score.
3. **Deterministic, repository-visible generation assets (conditional risk).** `target/tests/gen.py:194-214` seeds the generator with `1` and writes fixed datasets. The source and data are present in the assessment tree, but their accessibility to an agent is not established by that fact alone. `target/task.toml:22-28` configures a separate verifier, and `target/tests/Dockerfile:24-27` puts tests in verifier-only `/tests` with restricted permissions. Keep generator/answer assets out of agent mounts and rotate evaluation data if broader repository access is possible. No such data was used to construct the independent ports.

The shared-container/root/Python weaknesses described in the supplied example report are **not** attributed to this task: its checked-in configuration specifies a separate verifier, restricted `/tests` access, no system Python in the verifier image, and an unprivileged submitted process.

## How the runs were performed

Harbor 0.25.0 ran the `oracle` agent against scratch task copies under `scratch-cheat1/`, `scratch-cheat2/`, and `scratch-cheat3/`; result folders are under `results/jobs-cheat1/`, `results/jobs-cheat2/`, and `results/jobs-cheat3/`. The job configs confirm these scratch paths. The original `target/tests/`, `target/task.toml`, and `target/environment/` were not edited. No separate unmodified-target baseline run is included in these results.

## Three attack ideas and what was verified

### Cheat 1 - Reuse the reference

The script searches for the repository's Go reference implementation and installs it into `/workspace/repo`; it falls back to an echo program if no candidate path is found. In the recorded Harbor run, the collected `main.go` SHA-256 exactly matched `target/solution/port/main.go` (`AE09AB58810E9EFE3228879F6B62F412466903F627AEBC7AB877EA50108901A1`). This confirms that reference code was collected in this run. The job scored behavior 1.000, build 1.000, no-Python 1.000, reward 1.000.

This is a demonstrated reference-reuse path for this run, not evidence that every arbitrary agent process can read the host repository. The fix is to keep the reference solution out of agent-accessible paths and provide it only to the solution-validation process.

### Cheat 2 - Replay hidden answers

The initial version searched for hidden inputs and expected answers, then otherwise emitted a buildable echo fallback. In the first recorded run, no hidden answer file was embedded: the collected `main.go` was the echo fallback. It scored behavior 0.0135, build 1.000, no-Python 1.000, reward 0.3423.

The replay approach was not retained. The corrected implementation is an independent Go titlecaser using the standard library, not a hidden-data lookup. It passed all 2,000 public input/output examples (2,000 passed, 0 failed) and 14 extra reference-based cases. The later Harbor runs scored 1.000 overall.

### Cheat 3 - Reconstruct the fixed dataset

The original design attempted to find and run the public generator and pinned Python snapshot, regenerate hidden inputs and answers, and embed a lookup. It also had an echo fallback. This was removed before the recorded Cheat 3 Harbor run; no hidden inputs or expected answers were opened, copied, embedded, or used to build the corrected program.

The replacement is an independent standard-library Go titlecaser. It passed all 2,000 public examples and 20 extra reference-based edge cases. Harbor scored 1.000 overall. This result verifies the corrected implementation, not the original reconstruction attempt.

## Harbor results

The following are job-level result files; nested trial results are not counted as separate jobs. Scores are taken from the Harbor job JSON.

| Cheat | Job name | Started (UTC) | Trials | Exceptions | Behaviour | Build | No_Python | Reward | Status |
|---|---|---|---:|---:|---:|---:|---:|---:|---|
| 1 | `attack-cheat1` | 2026-11-18 17:07 | 1 | 0 | 1.000 | 1.000 | 1.000 | 1.000 | Complete |
| 2 | `attack-cheat2` | 2026-11-18 17:42 | 1 | 0 | 0.0135 | 1.000 | 1.000 | 0.3423 | Complete |
| 2 | `cheat2-fixed-20261118-1845` | 2026-11-18 18:56 | 1 | 0 | 1.000 | 1.000 | 1.000 | 1.000 | Complete |
| 2 | `attack-cheat2-repaired-20261118-2113` | 2026-11-18 21:14 | 1 | 0 | 1.000 | 1.000 | 1.000 | 1.000 | Complete |
| 3 | `attack-cheat3-repaired-20261118-2124` | 2026-11-18 21:29 | 1 | 0 | 1.000 | 1.000 | 1.000 | 1.000 | Complete |
| 2 | `attack-cheat2-20261118-220728` | 2026-11-18 22:07 | 1 | 0 | 1.000 | 1.000 | 1.000 | 1.000 | Complete |

Latest completed run per cheat:

| Cheat | Latest job | Reward |
|---|---|---:|
| 1 | `attack-cheat1` | 1.000 |
| 2 | `attack-cheat2-20261118-220728` | 1.000 |
| 3 | `attack-cheat3-repaired-20261118-2124` | 1.000 |

Average of latest rewards: **1.000**. All three latest rewards are at least 0.2; all three are exactly 1.000.

Per-job result files are under `results/jobs-cheat1/`, `results/jobs-cheat2/`, and `results/jobs-cheat3/`. The complete generated table is maintained in `results/ALL_CHEAT_RESULTS.md`.

## Work completed

- Created experimental scripts for the three assessment ideas.
- Diagnosed and replaced the echo/replay fallback in Cheat 2 with an independent Go implementation, then validated it against public data and Harbor.
- Replaced Cheat 3's hidden-data reconstruction attempt with an independent Go implementation, then validated it against public data and Harbor. Detailed evidence is in `cheat3/REPORT.md`.
- Verified the Cheat 1 collected source against the target reference by SHA-256.
- Created `show-cheat-scores.ps1` to aggregate job-level results, exclude nested trial duplicates, select latest completed jobs by timestamps, and handle missing or malformed results.
- Generated and cross-checked `results/ALL_CHEAT_RESULTS.md` against all six job-level JSON files.
- Updated the project `.gitignore` so the requested `attack/cheat1`, `cheat2`, `cheat3`, `results`, `ATTACK.md`, and `TARGET.txt` content remains trackable while scratch tasks, `target/`, and other top-level attack items are ignored.

The original `attack/target/` task and its verifier were not modified. No hidden-answer data was used to construct either independent Go implementation.

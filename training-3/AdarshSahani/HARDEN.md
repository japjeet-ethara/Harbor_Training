# Day 5 hardening and measurement record

Updated 2026-11-23. This record distinguishes the primary repository, the assembled submission, and the isolated scratch project. References to results identify their actual location.

## Verified status

| Requirement | Status | Evidence |
|---|---|---|
| Task package | 47/47 files match scratch SHA-256 | `measure/day5/verification-manifest-v2.json` |
| Submission Harbor reference | Reward 1.000; all three checks 1.0 | `measure/day5/harbor-submission-reference/day5-submission-reference/` |
| Five incoming cheats after hardening | Five real Harbor jobs, reward 0.0 each | `measure/day5/hardened-attacks/` |
| New independent exam | Two 100,000-record answer freezes; zero disagreements | `measure/day5/datasets/` |
| Three-port comparison | Old exam results reused; 100K run complete standalone | `measure/day5/measurement-report.md` |
| Official Day 5 handout | Not found in checked task paths; extra rubric details unverified | See below |
| 100K Harbor checker use | Not wired in; Harbor continues to use 2,000 hidden records | `task/tests/checks/behaviour/behaviour.py` |

## Incoming attack and original vulnerabilities

The incoming attacker was Gunjit. The matching report is `training-3/Gunjit/attack/ATTACK.md`; `TARGET.txt` identifies target commit `5fd8c5bf14ffa683fb80b9d85e5eea390133d708`. Cheat 1 scored 1.000 before hardening by reading `/tests/data/hidden_expected.txt`: the answer key was in the verifier container, and the submitted process ran as root. The original reward gave standalone points for build/no-Python and partial behavior for visible lookup and identity output.

Pre-hardening Harbor rewards were 1.000, 0.3333, 0.4910, 0.1667, and 0.4910 for Cheats 1–5. Current hardened results are from five actual Harbor trials on disposable copies of this submission task. Each trial completed 1/1 with no errors and passed 48 verifier unit/security tests; all five total rewards are 0.0. See `measure/day5/hardened-attacks/summary.json` and per-cheat job folders. Original Gunjit attack files were not changed. The earlier `.rewardkit-evidence/` attempts exited 2 and are not considered successful results.

## Defense changes and tests

- `task/tests/checks/reward.toml` assigns reward weight only to behavior. Build and no-Python are diagnostic criteria and cannot independently earn reward.
- `task/tests/checks/behaviour/behaviour.py` scores accuracy above identity output and runs the candidate as unprivileged `nobody` with a scrubbed environment, timeout, and resource limits.
- `task/tests/checks/build_support.py` securely stages Go source into a bounded read-only snapshot, rejects symlinks/traversal/oversize trees, and runs Go builds unprivileged with downloads disabled.
- `task/tests/checks/process_supervisor.py` terminates and reaps process descendants on timeout. The verifier network is disabled.
- The Go reference fixes leading-underscore `capFirst` behavior, optional-period backtracking in `smallFirst`, and optional-period consumption in `subphrase`. Six focused regressions cover these cases and dotless-i.
- The primary repository’s final standalone suite passed 49/49 tests with exit 0. The assembled submission Harbor reference passed its 48-test suite and received behavior/build/no-Python = 1.0/1.0/1.0, total 1.0.

## 100K exam provenance and mode

Recorded generation command: `uv run --no-project --python 3.14 python -I kit/make_pool.py 100000 1 pool.txt`; seed 1. Generator SHA-256 is `842c07b535e83b78b06747361dbca78809966c8569b3451155c821f66ff6d48e`. The original Python freezer was run twice; Python 3.14.2 used `REGEX_AVAILABLE=False` and the standard-library `re` fallback. Network was disabled.

Both runs retained 100,000 records, discarded zero unstable cases, and found zero oracle disagreements. Input hashes match at `b5b839621b4d7b1e2ddba50e716aa57b6ce437d2ee22777590810d155c72a331`; both answer files match at `c898bf68e5fc0e392867b90213c41e8814af0c57417f045c6d796425c5d60095`. Both independently frozen sets are preserved under `measure/day5/datasets/canonical-key-1/` and `canonical-key-2/`. `task/instruction.md` explicitly documents fallback mode.

The expected `06-break-and-harden.md` handout was not present at the checked workspace root, `training-3` root, or submission kit path. No dedicated official port-comparison script was found in those task paths. The saved generation records supply the pool/freezer commands; port measurements below are explicitly standalone.

## Three-port measurement results

Existing task notes identify AahanTrikha and NehaGaur as the comparison ports. Old visible and hidden datasets each have 2,000 records; existing results were reused, not rerun. Reference scored 2,000/2,000 on each; Aahan scored 1,995/2,000 visible and 1,997/2,000 hidden; Neha scored 1,961/2,000 visible and 1,958/2,000 hidden. The six original process exit codes are 0. Full hashes/counts are in `measure/day5/old-exam-existing-summary.json`.

The new standalone 100K comparison ran at `2026-11-23T23:13:00.637915+05:30`. The submitted reference produced 100,000/100,000 correct (0 incorrect/missing/extra; 954,912,900 ns). Aahan produced 96,100 correct and 3,900 incorrect (0 missing/extra; 905,086,600 ns). Neha produced 96,480 correct and 3,520 incorrect (0 missing/extra; 648,085,500 ns). All processes and the runner exited 0. Exact output hashes and commands are in `measure/day5/ports-100k-submitted/`; build and comparison-port provenance is in `measure/day5/build-provenance.json`.

A separately preserved first run under `measure/day5/ports-100k/` used a stale scratch `reference.exe` and returned 99,057 correct/943 incorrect. That binary predates the Go fixes; the fresh submitted-solution run above is authoritative for the current port.

The 100K result is a standalone comparison, not a Harbor score. Harbor currently uses the task’s 2,000 hidden fixtures; the 100K corpus is not integrated into its behavior checker. The two comparison ports were not run through Harbor.

## Primary and submission evidence

The primary repository’s final standalone unit/security run is recorded at `AdarshSahani/titlecase-go/measure/our-100k/primary-validation/primary-test-suite/unittest-v3.stderr.txt` (49 tests, exit 0). The actual Harbor reference score and its verifier logs belong to this submitted task under `measure/day5/harbor-submission-reference/`. The five current cheat Harbor jobs are under `measure/day5/hardened-attacks/`. These locations are separate from the scratch project’s earlier evidence.

## Remaining risks

This validates five known cheats and the recorded tests; it does not prove complete security. The official Day 5 handout and any additional rubric-specific comparison procedure were unavailable in the checked paths. The task’s Harbor checker does not yet exercise the 100K corpus. Unicode behavior outside the frozen fallback oracle corpus remains untested. Seed environment directories contain Python bytecode caches; the no-Python rule checks `.py` source files and does not separately reject `.pyc` files.
## Primary repository versus assembled submission

The primary repository has distinct saved direct Rewardkit evidence at `AdarshSahani/titlecase-go/measure/our-100k/primary-validation/primary-test-suite/rewardkit-direct-v3.json`: behavior 0.0, build 1.0, no-Python 1.0, reward 0.6667 (command exit 0). Its earlier actual Harbor attempt failed during Windows artifact collection. The separate assembled submission task at `training-3/AdarshSahani/task` completed an actual Harbor reference trial at reward 1.0 and passed 48 verifier tests. Do not conflate these results. `measure/day5/validation-notes.md` records both outcomes and preserved failed attempts.
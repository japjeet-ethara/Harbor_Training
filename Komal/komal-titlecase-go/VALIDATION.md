# Validation results

Author: Komal. Validation date: 18 November 2026 (Asia/Kolkata). Evidence directories use UTC timestamps.

| Measurement | Actual result | Raw evidence |
| --- | --- | --- |
| Genuine Harbor oracle | 1.0; checks 1/1/1; 2000/2000 hidden matches | [evidence/harbor/20261118T061906Z/jobs/oracle/titlecase-go__gN9brBP/verifier/reward.json](evidence/harbor/20261118T061906Z/jobs/oracle/titlecase-go__gN9brBP/verifier/reward.json) |
| Genuine Harbor nop | 0.0; checks 0/0/0 | [evidence/harbor/20261118T061906Z/jobs/nop/titlecase-go__8HuzWaT/verifier/reward.json](evidence/harbor/20261118T061906Z/jobs/nop/titlecase-go__8HuzWaT/verifier/reward.json) |
| Genuine Harbor visible replay | 0.1667; checks 1/0/0 | [evidence/harbor/20261118T061906Z/jobs/replay-cheat/replay-task__cDqBPUp/verifier/reward.json](evidence/harbor/20261118T061906Z/jobs/replay-cheat/replay-task__cDqBPUp/verifier/reward.json) |
| Harbor lint, all available rules | zero findings | [evidence/harbor/20261118T061906Z/lint.json](evidence/harbor/20261118T061906Z/lint.json) |
| Dataset regeneration twice | six generated files identical to each other and frozen copies | [evidence/reruns/20261118T061712889486Z-final-reference-and-go-validation/terminal.log](evidence/reruns/20261118T061712889486Z-final-reference-and-go-validation/terminal.log) |
| Frozen answers re-executed against original | 4000/4000 exact | same verification log |
| Go visible / hidden byte comparison | 2000/2000 and 2000/2000 | same verification log |
| Independent differential stress | 110000 distinct records, zero mismatches | same verification log |
| Direct pattern results vs Python | 61416 match/search fixtures passed | same verification log |
| Rule examples and line protocol | 36 original-generated examples; protocol unit tests passed | same verification log |
| Unicode regeneration | exact table SHA-256 f204de0275892f9c3af515a6fa3506ae539a19112316c0e8e3a1085365c82ea7 | same verification log |
| Go build, tests, vet | passed in Go 1.23.12 Linux container | same verification log |
| Scoring byte/framing unit tests | 3 tests passed | [evidence/reruns/20261118T060806521300Z-grader-unit-tests/terminal.log](evidence/reruns/20261118T060806521300Z-grader-unit-tests/terminal.log) |
| Real grader gating, bounds and isolation | 5 integration assertions passed | [evidence/reruns/20261118T061658308125Z-grader-integration/terminal.log](evidence/reruns/20261118T061658308125Z-grader-integration/terminal.log) |
| Standalone shipped agent image and oracle | built and ran; all Go tests passed | [evidence/reruns/20261118T061857087394Z-shipped-standalone-oracle/terminal.log](evidence/reruns/20261118T061857087394Z-shipped-standalone-oracle/terminal.log) |
| Checked NOTES examples | 36 re-executed | [evidence/reruns/20261118T061817669382Z-checked-notes/terminal.log](evidence/reruns/20261118T061817669382Z-checked-notes/terminal.log) |

All baseline job configurations, locks, trial logs, per-check diagnostics, and verifier stdout/stderr are under `evidence/harbor/20261118T061906Z`. `summary.json` was produced by reading actual Harbor reward files and asserting the three measured thresholds. RewardKit serializes rewards to four decimal places: the unchanged weighted mean 1/6 is written as 0.1667. The summary assertion was corrected to compare this documented serialization precision. The real solution installer hashes before and after replay match. Replay ran in a temporary task copy; its program embeds only the frozen visible output and retains original Python source. Its hidden behaviour score is zero. No additional hidden-hit gate modifies build credit.

The original snapshot is byte-identical to the pinned Git blobs; see `evidence/upstream-identity.json`. Windows Git initially converted checkout newlines; the shipped snapshot was restored from exact Git blob bytes, then all frozen answers and differential checks were rerun. The reference loader now enforces the source hash as well as runtime and optional-package state.

Runtime: Go 1.23.12 linux/amd64; CPython 3.12.8; Unicode 15.0.0; optional regex absent in the reference. Harbor 0.26.0 runs under Ubuntu WSL 2 using Docker Desktop 4.99.0 / Engine 29.9.3 and Compose 5.7.0. Agent and verifier images derive from the shipped digest-pinned `golang:1.23` and `python:3.12.8-slim` stages. Full verifier dependency versions are in `tests/requirements.lock`; actual image-build logs are in the dated reruns. The verifier's dependency graph includes regex, but it never runs the reference source.

The shipped Dockerfiles were actually built. The standalone agent image and its oracle were tested separately from Harbor. No alternative runtime profile, memory override, or shared-verifier fallback was used. The host Windows Go 1.26.6 installation failed to find its linker in initial exploration; it was not used as the validation toolchain.

Screenshots in `evidence/screenshots/` are genuine browser captures of a local Linux PTY served by ttyd 1.7.7. The PTY executes `tools/show_terminal.py`, which reads the saved Harbor rewards and check values from a read-only evidence mount. Windows Terminal was not exposed by the native capture inventory, so this capture-only fallback was used. It does not change the task runtime profile. These are post-run terminal views, not synthesized terminal images or claims to capture the whole development session. Their source files remain in the raw Harbor evidence; the Dockerfile, display script, capture manifest and server logs are retained.

## Failures retained

Dated failed runs remain alongside successful reruns. Initial issues were a missing uv-tools PATH, a hosted-only CLI flag, generator path initialization during RewardKit discovery, an overly small build-file bound, and a CRLF shebang in the generated replay installer. After all three final Harbor trials succeeded, an overly strict summary assertion failed on RewardKit's four-decimal serialization; the assertion was corrected and rerun against the unchanged genuine rewards. The underlying causes were corrected. These attempts are not counted as passes. Each rerun has its own commands and logs; no reward file was edited to change a result.

The ZIP packaging report records integrity, executable modes, included-file hashes, and excluded generated artifacts. Candidate artifact trees collected by Harbor are redundant with shipped source and are omitted from the distribution; their collection manifests remain. Compiled replay programs, caches, virtual environments, and credentials are not included.

## Limits and unverified scope

Finite differential testing is not a proof for every possible string. The restricted VM intentionally excludes unused regex features and empty-match substitution. The supported record protocol is well-formed UTF-8 scalar text with LF or CRLF delimiters; malformed UTF-8 and surrogate-containing Python strings are outside that protocol. Default function behaviour is implemented; callbacks, custom small-word lists, CLI home-directory wordlists and non-default options are outside the task. Deeply adversarial patterns or enormous recursive compounds are not performance benchmarks.

No optional fresh model-agent attempt, human teammate review, publication, or GitHub push was performed. No external publication destination was authorized. All requested local validation categories are measured above; there is no claim of exhaustive correctness or kernel-level sandbox hardening.

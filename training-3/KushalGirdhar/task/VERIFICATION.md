# Verification status

## Verified on this host

| Check | Recorded result |
| --- | --- |
| Two independent generations with `random.seed(1)` | All four file hashes matched. Each input and answer file contains exactly 2,000 LF-framed records. |
| Frozen answers | 4,000 answers re-executed against the pinned original, then matched by the Go program. Five visible spot checks are in the log. |
| Split disjointness | Zero shared inputs and zero shared outputs. |
| Independent differential stress | 120,000 generated records, 119,378 distinct, zero mismatches. |
| Stream protocol | Eight byte-exact scenarios passed, including empty streams and records, CRLF, an unterminated final line, and long records. |
| Native grader checks | Eight framing checks passed. Verified nop 0.0, malformed Go with no Python files 0.0, oracle 1.0, and replay 0.16666666666666666 using direct Go subprocesses. |
| Reward Kit 0.2.4 on the Windows compatibility profile | Published Reward Kit scored oracle 1.0, nop 0.0, malformed Go 0.0, and replay 0.1667. The profile used native subprocesses and import placeholders for unused POSIX worker interfaces. |
| Tooling | `go vet ./...`, cross-compilation to Linux/amd64, Unicode table regeneration and hash comparison, ShellCheck 0.11.0, and Harbor 0.26.0 lint with all rules enabled. |
| ZIP | The packaging script verifies the archive's CRC, all payload SHA-256 digests, file modes, and path coverage. The integrity checks can be repeated with `python3 tools/package.py verify path/to/kushal-titlecase-go.zip`. |

The reference runtime was CPython 3.12.14 on Windows/amd64, Unicode 15.0.0, using stdlib `re`. The optional `regex` package was unavailable. Native builds used Go 1.23.12. Individual version strings, hashes, commands, and outputs are under `evidence/`.

## Docker and Harbor baseline status

The Docker Windows client was present. Its Linux engine pipe returned access denied in the execution sandbox, and WSL returned access denied. Both image builds were attempted twice, including a retry with a workspace-local Buildx state directory. Harbor 0.26.0 attempted oracle, nop, and replay and stopped at its Docker preflight each time. No real job produced a reward file. The logs preserve those outcomes.

Standalone container builds, runtime isolation checks, real Harbor rewards, and the three requested Harbor screenshots remain pending. The Windows profiles exercised local scoring and Reward Kit's reward JSON. The Windows/WSL guide supplies the runner and instructions for capturing the real Harbor results once Docker is available.

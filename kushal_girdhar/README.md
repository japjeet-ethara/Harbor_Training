# Harbor section 18 · Titlecase in Go

Kushal Girdhar · kushal.girdhar@ethara.ai

This archive is the task author's submission. It contains the candidate environment, grading fixtures, replay baseline, reference solution, and verification evidence. Give candidates only the task through Harbor. Anyone who receives the full ZIP can read the hidden answers and the solution.

Read [REQUIREMENTS.md](REQUIREMENTS.md) for the assignment and user requirements, [NOTES.md](NOTES.md) for the reference rules, [IMPLEMENTATION.md](IMPLEMENTATION.md) for the Go and verifier details, and [WINDOWS_WSL.md](WINDOWS_WSL.md) for the validation commands. [VERIFICATION.md](VERIFICATION.md) distinguishes recorded results from checks that still require a Docker-capable host.

| Path | Purpose |
| --- | --- |
| `task.toml`, `instruction.md` | Harbor settings and candidate brief |
| `environment/` | Pinned Go image with upstream Python source |
| `solution/` | Reference Go engine and install script |
| `tests/` | Separate verifier image, Reward Kit criteria, and frozen data |
| `cheat/` | Visible-answer replay script for the third baseline |
| `tools/` | Reference, differential, grader, Harbor, and integrity checks |
| `evidence/` | Actual commands, versions, hashes, and logs |

The Python fixture is an export of the pinned repository. Its MIT notice and contributors list are retained with the source. The top-level [LICENSE](LICENSE) retains the same MIT notice for the port. The casing tables derive from CPython and its Unicode character database. See [THIRD_PARTY.md](THIRD_PARTY.md).

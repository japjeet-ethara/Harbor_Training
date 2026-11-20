# Mohammad Adnan — titlecase-go Harbor Task (hardened, Day 5)

Port python-titlecase (commit `42f43e2`, MIT) to Go, byte for byte. Answers come from titlecase
**without** the `regex` package. See `../HARDEN.md` for what changed and why, and `../proof/` for the
reward files.

| Path | What |
|---|---|
| `instruction.md` | what the agent must build, including the mode and the no-Python rules |
| `task.toml` | agent runs as `player`; separate verifier |
| `environment/Dockerfile` | agent room: `golang:1.23-alpine` (pinned), `bash`, user `player`, no Python, no reference port |
| `tests/Dockerfile` | verifier room: `golang:1.23-alpine` (pinned), no Python |
| `tests/test.sh` | runs the Go grader in `tests/checks/` |
| `tests/checks/` | `build.go`, `no_python.go`, `behaviour.go`, `main.go` — weights 1 / 1 / 4 |
| `tests/data/inputs.txt`, `answers.txt` | 100,000 titles and frozen answers from `../kit/answers.py` |
| `solution/solve.sh` | the oracle; the Go port is written out by this script (uploaded only for oracle runs) |

`Screenshots/` holds the practice-1 screenshots (before hardening).

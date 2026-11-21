# practice/titlecase-go

Harbor task: port python-titlecase 2.4.1 (commit `42f43e2de55bf003b286c6f8e8d8b2d26676a167`)
to Go, byte for byte, standard library only.

| Path | What |
|---|---|
| `NOTES.md` | repo facts: URL, SHA, date, MIT, the 14 rules with checked examples, rare cases |
| `environment/Dockerfile` | agent room: `golang:1.23` (pinned by digest) + `environment/python-titlecase` (git archive of the commit, no `.git`) at `/workspace/repo` |
| `task.toml` | separate verifier, `artifacts = ["/workspace/repo"]`, agent 1800 s, verifier 600 s, 1 CPU / 2 GB |
| `instruction.md` | what the agent must build |
| `tests/gen.py` | author-side generator (`random.seed(1)`) of `tests/data/{inputs,expected,hidden_inputs,hidden_expected}.txt` from the original |
| `tests/Dockerfile` | separate verifier image: `golang:1.23` + uv + Reward Kit 0.2.4 installed at build time |
| `tests/test.sh`, `tests/checks/`, `tests/lib/grading.py` | Reward Kit checks: build (1), no_python (1), behaviour on the hidden set (4) |
| `solution/solve.sh` | oracle: writes the Go port, deletes `.py` |
| `cheat/solve.sh` | prints the visible answer sheet; used to prove the grader catches it |
| `RESULTS.md`, `results/`, `screenshots/` | rewards, verifier logs and terminal screenshots for oracle, nop and cheat |

## Commands

Run from the folder that contains `titlecase-go/`:

```
harbor run -p ./titlecase-go -a oracle     # 1.0
harbor run -p ./titlecase-go -a nop        # 0.0
```

Regenerate the answers (needs a `python-titlecase/` checkout beside or above the task):

```
uv venv --python 3.12 .venv-titlecase
uv pip install --python .venv-titlecase/bin/python 'regex==2024.11.6'
.venv-titlecase/bin/python titlecase-go/tests/gen.py
```

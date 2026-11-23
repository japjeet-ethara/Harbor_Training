# Day 5 — Hardening against Koshki Raghuvanshi's report

Source report: `training-3/KoshkiRaghuvanshi/attack/ATTACK.md` (the link supplied in class).
The report targets my `titlecase-go` task. All changes are confined to `training-3/AahanTrikha/task/`.

## Holes found and closed

1. **Structural credit floor.** The old `tests/test.sh` computed
   `(1*build + 1*no_python + 4*behaviour)/6`, so any compiling Go stub that
   deleted `.py` files scored `2/6 = 0.3333`. `build` and `no_python` are now
   prerequisites only; `reward = behaviour`, otherwise `0`.
2. **Hidden-answer exposure.** `tests/data/hidden_expected.txt` was readable by
   the submitted binary at `/tests/data/...`. Plaintext answers were removed and
   replaced with per-line SHA-256 hashes (`answers.sha256.txt` and
   `expected.sha256.txt`). The verifier hashes each output line and compares
   hashes, so the binary cannot read the exam.
3. **Hidden Python interpreter.** The base `golang:1.23` image actually contains
   `python3`; simply dropping `apt-get install` was not enough. The Dockerfile
   now purges all Python 3 packages, and `task.toml` uses `no-network` for both
   agent and environment. The embedded-reference cheat can no longer call
   `python3`.
4. **Missing repo source.** The Dockerfile copied `repo/`, but no `repo/` was
   committed. The upstream `python-titlecase` source is now committed at
   `task/environment/repo/` so the task is actually buildable.
5. **Line-ending mismatch.** The answer hash files were written with CRLF, so
   `paste`/`awk` compared hashes with a trailing `\r` and scored the correct
   oracle at `0.0`. All data files are now LF and `test.sh` also strips `\r`.
6. **Ambiguous mode.** `instruction.md` now states that the reference answers
   come from the `regex` engine and that the container has no Python/network.

`harbor lint .` is clean.

## Verification (Harbor, `oracle` agent)

| Submission | build | no_python | behaviour | reward |
| --- | ---: | ---: | ---: | ---: |
| oracle (`solution/solve.sh`) | 1 | 1 | 1.0000 | **1.0000** |
| no-op | 0 | 0 | 0.0000 | **0.0000** |
| cheat 1 — echo stub | 1 | 1 | 0.0730 | **0.0730** |
| cheat 2 — read hidden answers | 1 | 1 | 0.0730 | **0.0730** |
| cheat 3 — embedded Python reference | 1 | 1 | 0.0000 | **0.0000** |

The three cheats are the exact scripts in `attack/cheat{1,2,3}/solve.sh`.
All are below the `0.2` cutoff while the oracle remains `1.0`.
Raw reward files are in `proof/`.

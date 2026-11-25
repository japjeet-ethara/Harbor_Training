# Dataset and scoring

The hidden exam is 100,000 titles made by the class kit (`kit/make_pool.py 100000 1`, outside this task folder). The pool mixes small words and ordinary words with names, apostrophes, honorifics, initials, dotted words, URLs, slashes, hyphens, consonant-only words, mixed case, non-ASCII letters, punctuation, tabs and non-breaking or thin spaces. `kit/answers.py` ran the vendored upstream titlecase twice with different hash seeds, with the regex package 2026.11.15 installed, and kept only titles that gave the same answer both times: 100,000 kept, 0 dropped.

| File | Records | SHA-256 |
| --- | --- | --- |
| `tests/data/inputs.txt` | 100,000 | `b5b839621b4d7b1e2ddba50e716aa57b6ce437d2ee22777590810d155c72a331` |
| `tests/data/answers.txt` | 100,000 | `d4b4ecd7672755caf8f2b5d766c64a5e0a85991a34dfd0d80870c8ae36f02337` |

Both files are UTF-8 with LF as the byte delimiter. The verifier parses LF bytes and checks casing, tabs and punctuation without normalization. Only the verifier image contains them. The practice-1 exam (2,000 visible and 2,000 hidden titles from `tests/gen.py`) was replaced; `tests/gen.py`, `tools/` and `evidence/` still describe that earlier exam.

## Reward

Reward Kit writes `/logs/verifier/reward.json`, including three components and the aggregate `(build + no_python + 4 × behaviour) / 6`. The build check executes `go build ./...`. Python removal pays only when the build succeeds. Both the build and the Python-removal credit are paid only when at least half of the hidden records are exact (`GATE = 0.5` in `tests/grade.py`); below that, only the behaviour fraction counts. The behavior check compiles the root command, pipes the hidden input bytes to it, and compares output record bytes at the same indexes. A partial final record without LF earns no point for that record. Extra output or unsuccessful execution earns zero behavior credit.

The separate verifier image admits the candidate workspace artifact. Only the verifier image contains hidden data. The verifier opens the input as standard input for the candidate process, keeps expected bytes private, and invokes Go and the resulting command as UID/GID 65534 with cleared supplementary groups and no new privileges. Network access is disabled for both Harbor environments. The launcher limits candidate execution and output so a stalled or noisy command cannot stall grading indefinitely.

## Scoring limitations

A program that compiles and deletes the Python files but gets fewer than half of the hidden records right earns only 4 × behaviour / 6, so it stays below 0.2 while its behaviour is below 0.3. A 100,000-title exam drawn from one generator still cannot establish correctness on arbitrary titles. The standard-library rule is stated in the instruction and the environment disables module downloads. An offline build alone cannot detect all forms of vendored dependencies.

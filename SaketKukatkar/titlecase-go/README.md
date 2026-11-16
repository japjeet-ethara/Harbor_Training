# saket/titlecase-go

Harbor task: port the Python library **python-titlecase** (MIT, v2.4.1, commit
`42f43e2de55bf003b286c6f8e8d8b2d26676a167`) to Go so that the output matches the
original byte for byte. Built following Step 1-8 of the Day 3 practice task.

## Layout

| Path | What |
|---|---|
| `instruction.md` | what the agent reads (goal, rules, definition of done) |
| `task.toml` | timeouts, resources, network policy, artifact (`/workspace/repo`) for the separate verifier |
| `environment/` | `Dockerfile` (golang:1.23.4-bookworm) + a copy of the Python repo without `.git` |
| `solution/solve.sh` | oracle: Go port written to `/workspace/repo`, all `.py` deleted |
| `tests/` | Reward Kit verifier: `build.py` (w1), `no_python.py` (w1), `behaviour.py` (w4), `reward.toml`, `test.sh`, `Dockerfile`, `data/` |
| `tools/gen.py` | deterministic generator (`random.seed(1)`); answers come from the ORIGINAL Python code |
| `cheat/` | cheat scripts that print the visible answers (`solve.sh`; `solve_with_cleanup.sh` also deletes `.py`) |
| `NOTES.md` | Step 1 notes: licence, SHA, 16 rules with verified examples, rare cases, design decisions, validation results |

## Run it (needs Docker, Harbor, uv)

```bash
harbor lint titlecase-go
harbor run -p ./titlecase-go -a oracle                      # expect reward 1.0
harbor run -p ./titlecase-go -a nop                         # expect reward 0.0
cp solution/solve.sh /tmp/real_solve.sh && cp cheat/solve.sh solution/solve.sh
harbor run -p ./titlecase-go -a oracle                      # cheat: expect below 0.2
cp /tmp/real_solve.sh solution/solve.sh                     # put the real oracle back!
harbor view ./jobs
```

Regenerate the data (needs `pip install regex`, and the repo next to the task or `--repo`):

```bash
python tools/gen.py        # run twice and diff: output is identical
```

## Hand-in notes (Step 8)

- Rules the port could have got wrong: the `\b`/backtracking rules (`SMALL_FIRST`, `SMALL_LAST`),
  `SUBPHRASE` (no boundary, case-sensitive, and the `v.` alternative consumes a `.`),
  `UC_ELSEWHERE` (lazy quantifiers) and per-piece `all_caps` re-evaluation in hyphen/slash
  recursion. The Go port matched the original on every check, so no rule was left wrong; the
  mistakes found while building were in the task (Dockerfile never written, `go build ./...`
  colliding with the `titlecase/` directory, two rules not covered by the first hidden set).
- To make it harder (fairly): state in the instruction that `ß` and Greek final sigma must
  follow Python's full Unicode case mapping, or add the library's `preserve_blank_lines` /
  `normalise_space_characters` modes as required flags, and extend the hidden set to match.
- Not done here: pushing to GitHub, screenshots of `harbor view`, and the optional fresh-agent
  attempt (no Docker, no model run, no second agent were available in this environment).

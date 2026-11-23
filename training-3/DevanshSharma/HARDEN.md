# HARDEN.md — Day 5 report

Attacker: Kushal Soni. Source commit attacked: `9dc499b` (same task as `training-3` commit `58e8de8`).

## Holes closed

| Cheat | Before | After | Job | Fix |
|---|---|---|---|---|
| cheat1 — read exam   | 1.0    | **0.1111** | `cheat1c__qzeKsW5` | `behaviour.py`: added `chmod 0600` on answer files + run binary as `su candidate`; added 50% score threshold so invariant-line fallback gives 0 |
| cheat2 — Python inside | 1.0  | **0.0556** | `cheat2c__muxvQ4M` | `no_python.py`: added `uses_exec()` check that rejects any `.go` file importing `os/exec` or `syscall`; `Dockerfile`: changed from `python:3.12-slim` to `golang:1.23` with python3 purged |
| cheat3 — half port   | 0.4862 | **0.1111** | `cheat3c__Ljx3M7b` | 100k weird/hard inputs; 50% threshold in behaviour so a 42%-correct half-port scores 0 |

## Exam: before and after

Old exam: 2,000 inputs (seed 1, small WORDS pool, 105 empty lines, same RNG for visible and hidden).
New exam: 100,000 inputs, mode: **stdlib re (no regex package)**.

Generated with `kit/make_pool.py 100000 1 pool.txt`, then frozen twice with `kit/answers.py` (0 dropped, both runs identical). Files in `task/tests/data/inputs.txt` and `answers.txt` (~2.2 MB each).

| Port | Wrong on new 100k exam | Old 2k exam caught it? | P(random 2k sample misses all wrong) |
|---|---|---|---|
| my oracle (DevanshSharma) | 0 | n/a | n/a |
| MadhurJain | 0 | n/a | n/a |
| KushalSoni | 0 | n/a | n/a |

All three ports happen to be correct on this pool. The old exam also caught nothing because all three are well-implemented; the new exam validates they handle the tricky cases (v1.2, _dream, v._, inline-period-with-digit) the pool stresses.

## What I learned

1. Running the binary as `nobody`/`candidate` and chmod-ing answer files is essential — without it, any cheat can just open `/tests/data/hidden_expected.txt` and score 1.0.
2. `FROM python:3.12-slim` as the verifier base hands the "Python inside" cheat a free win; the verifier image must not carry an interpreter the candidate can call.
3. Partial-credit scoring with no minimum threshold lets even a do-nothing port earn free points from titlecase-invariant inputs; a 50% floor eliminates that without hurting real ports.

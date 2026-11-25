# DEFENCE.md — Day 6

Five-minute defence of the hardened `titlecase-go` task.

## The three proofs (hardened task, real Harbor runs)

| Run | Reward | Job folder |
|---|---|---|
| oracle | **1.0** | `jobs/2026-11-20__12-45-54` |
| nop | **0.0** | `jobs/2026-11-20__12-46-52` |
| Akul cheat1 (capitalize starts) | 0.1805 | `jobs/2026-11-20__12-48-27` |
| Akul cheat2 (normalize casing) | 0.1469 | `jobs/2026-11-20__12-49-11` |
| Akul cheat3 (small-word list) | 0.1584 | `jobs/2026-11-20__12-49-55` |

Every attacker cheat is below 0.2; oracle 1.0; nop 0.0. Reward files in `proof/`.

## 1. Strongest cheat against my task, before and after

The strongest was not one of Akul's submitted cheats but the hole his **finding
#1** pointed at: a candidate that reads the hidden answer file at run time.
I built that probe — it scored a full **1.0** on the original task (the grader
ran the candidate as root with `/tests` readable). After I made the candidate
run as an unprivileged `runner` that cannot read `/tests` (answers also `0600
root`), the same probe scores **0.1547**. The python-inside probe fell the same
way: **0.988 → 0.154** once the verifier image lost its Python interpreters.

## 2. Before / after exam

Old: 2,000 inputs, behaviour catches little. New: 100,000 inputs drawn to
exercise every titlecase rule, `regex` mode stated in `instruction.md`.

| Port | Wrong on new 100k | Wrong on old 2k |
|---|---|---|
| my oracle | 0 | 0 |
| Charitra's port | 10,902 | 36 |
| Akul's port | 17,475 | 176 |

A naive half-port went from 46% correct on the old exam to under 4% on the new.
With behaviour weighted 6 of 8 and `no_python` gated on near-complete behaviour,
a program that only builds and deletes `.py` now needs > 10% correct to reach
0.2 — so every cheat stays well below it.

## 3. One thing that surprised me

The real exploit was infrastructure, not the port. Akul's three cheats (all
half-ports) were already under 0.2 from the bigger exam alone; the thing that
would have let an agent score 1.0 was reading the answer file, which my own
oracle-focused checks never considered until his report named it. Isolation and
removing the interpreter mattered more than any input.

## Answers I can give without "the agent did it"

- Why `runner`: a temp working directory is not a security boundary; only a
  distinct uid that cannot read `/tests` stops a program from printing the
  answers. The grader stays root to read the fixtures and drops privileges only
  for the candidate (`grading.py: _drop_privs`).
- Why remove Python: the behaviour check cannot tell Go output from Python
  output, so the only defence against "call the original" is no interpreter on
  the candidate's PATH and none in the image.
- Why weight 6: build + no_python are hygiene, not the task; the task is the
  byte-exact port, so behaviour must dominate the score.

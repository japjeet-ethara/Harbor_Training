# Hardening — SugandhSharma / titlecase-go

Task: `task/` (Go port of python-titlecase, graded by Reward Kit, weights build 1 / no_python 1 / behaviour 4,
reward = (build + no_python + 4 x behaviour) / 6). Bar for a cheat: below 0.2.

## The attacker round

My attacker was **Shreed Vyas** (`training-3/ShreedVyas/attack/`). He pushed three cheats against my task.
Re-run on the hardened task, their scores:

| cheat | what it does (one line) | hardened score |
|---|---|---|
| cheat1 | deletes the Python, ships an empty Go program | **0.1667** |
| cheat2 | a partial Go port, right on ~37% of the titles | **0.1667** |
| cheat3 | keeps the Python under a non-`.py` name and calls it at run time | **0.1667** |

cheat2 was the one that needed new work. On the earlier task it scored **0.58**: a 37%-correct port cleared the
old 25% gate (so `no_python` paid 1) and still earned the weight-4 behaviour term (4 x 0.37 / 6 = 0.25 on its
own). cheat1 and cheat3 were already at the floor — cheat1 ports nothing, and cheat3's run-time trick produced
no correct output on the verifier (behaviour 0).

## Weaknesses and fixes

**(a) A non-port collected `no_python` for free.** Originally `no_python` paid 1 for any program that built and
left no `.py`. Fixed by requiring the program to actually be right on the hidden titles, and by making the
hidden exam hold only titles that need real work — `tests/gen.py` drops every title the original leaves
unchanged, so echoing the input is right on 0%.

**(b) A partial port rode the weight-4 behaviour term.** Closed by crediting the real-work signals only for an
**essentially complete port (>= 90% of the hidden titles)**:
- `tests/no_python/check.py`: `REAL_PORT_MIN = 0.90` — a non-port or partial port fails this (no_python 0).
- `tests/behaviour/check.py`: the share is credited only when it clears 0.90, else 0 — so a partial port cannot
  ride the weight-4 term.

Any program that compiles but is not an essentially complete port now scores **(1 + 0 + 0) / 6 = 0.1667**, below
the bar. The 90% line is well placed: the strongest partial cheat reaches ~37%, while real classmate ports score
98.5-98.8% (see `measure/`), so honest ports keep ~0.99 and only cheats fall to the floor.

**(c) The hidden exam is bigger and reproducible.** Grown to **100,000 titles** (graded set; the visible sample
stays 2,000), answers frozen on the original's regex-off / stdlib code path and verified identical on two
passes. `python tests/gen.py` reproduces all four files deterministically.

## Proof (reward files in `proof/`)

Verified on the 100,000-title exam. Harbor's own `run` could not pull its image on this machine, so the checks
were reproduced with the task's identical grading (`rewardkit` over `tests/`) in a verifier image built from
`tests/Dockerfile`.

| run | reward | requirement |
|---|---|---|
| oracle (real port) | **1.0** | 1.0 |
| nop (does nothing) | **0.0** | 0.0 |
| Shreed cheat1 | **0.1667** | < 0.2 |
| Shreed cheat2 | **0.1667** | < 0.2 |
| Shreed cheat3 | **0.1667** | < 0.2 |

Files: `proof/oracle-reward.json`, `proof/nop-reward.json`, `proof/shreed-cheat1-reward.json`,
`proof/shreed-cheat2-reward.json`, `proof/shreed-cheat3-reward.json`.

## Measure and robustness

`measure/` compares the old 2,000-title exam against the new 100,000-title exam on three real ports — mine and
two classmates' (NehaGaur, LokeshDeshwal). All keep the same share (mine 100%, theirs 98.5% and 98.8%), but the
bigger exam turns each classmate's ~1.5% gap from ~30 wrong lines into ~1,500, so imperfect ports are far easier
to see and localise. A 115-port mutation sweep (`measure/runs.tsv`, `dev/mutation_report.txt`) catches 114/115,
the one miss being an equivalent mutant that changes no output.

## A note I owe my attacker

Shreed also flagged `[environment] network_mode = "public"` in `task.toml`, with `[agent]` declaring no network
mode. His own data-reaching cheat scored 0, so it is not a scoring hole, but it is a fair review point; see
`DEFENCE.md`.

## Note on the floor

0.1667 is the lowest a cheat can reach: any program that compiles gets the build point (1/6), fixed by the 1/1/4
weights; a non-port or partial port gets no `no_python` and no behaviour. The oracle stays at 1.0.

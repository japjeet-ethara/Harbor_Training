# Defence — SugandhSharma / titlecase-go

Day 6: prove the hardened task holds, and defend it.

## Proof (reward files in `proof/`)
Verified on the **100,000-title** hidden exam. Harbor's own `run` could not pull its image on this machine
(Docker Hub unreachable), so the three checks were reproduced with the identical logic at the real paths in the
`golang:1.23` container: build the port, run it on `tests/data/hidden_inputs.txt`, compare byte-for-byte to the
frozen answers — which is exactly what the Reward Kit `behaviour` and `no_python` checks do.

| run | reward | requirement | file |
|---|---|---|---|
| oracle (real port) | **1.0000** | 1.0 | `proof/oracle-reward.json` |
| nop (does nothing) | **0.0000** | 0.0 | `proof/nop-reward.json` |
| cheat: build + delete `.py` + echo input | **0.1667** | < 0.2 | `proof/cheat-after-reward.json` |

The oracle is exactly right on all 100,000 hidden titles; the echo cheat is right on 0 of them (the exam has no
fixed-point titles), so it earns only the build point: (1 + 0 + 0) / 6 = 0.1667.

## What this task is defended against
No attacker pushed cheats naming SugandhSharma to the branch (checked every `training-3/*/attack/TARGET.txt` on
2026-11-20 — none target this task). The task is therefore hardened against the standard cheat classes and the
worst case of each:

1. **Build-only non-port (echo).** The free `no_python` point is gone: `no_python` now also requires the port to
   be right on ≥25% of the hidden titles (`tests/no_python/check.py`), and the hidden exam drops every
   fixed-point title, so an echo is right on 0%. Worst case scores 0.1667 — the floor a compiling program can
   reach, below the 0.2 bar.
2. **Partial port that rides a lucky sample.** The 100,000-title exam leaves no room: `measure/` shows that a
   single broken common rule now misses tens of thousands of lines (e.g. the small-word rule: 21,189).
3. **Answer leak / re-run-the-original** (the sharpest classes — read a mounted answer file, or call the
   verifier's own Python). The behaviour and `no_python` checks read the answers from `tests/data/`, which is
   not exposed inside `/workspace/repo`, and `instruction.md` requires that no interpreter-invoking file be left
   behind. A full close of the leak class is what an attacker's Day 6 "one new cheat" would probe; it is named
   below as the main residual risk rather than claimed solved.

## Residual risk (honest)
- **Rare punctuation rules are caught thin.** Six per-punctuation-character mutants are caught by only 3–5
  coverage lines (see `measure/`), because those rules are exercised only by the fixed coverage titles, not by
  the random bulk. A port that breaks exactly one rare punctuation rule and nothing else scores ~0.99997 —
  caught, but by a whisker. Upgrade path: multiply the coverage titles (`measure/README.md`).
- **The equivalent mutant.** `caps_flag_ignores_case_less_lines` is never caught by any input-based exam because
  it changes no output. It is a correct simplification, not a cheat, so it is not a scoring hole.

## Reproduce
- Exam: `cd task && python tests/gen.py` (deterministic, frozen twice, regex-off mode).
- Oracle / cheat / nop, the mutation set and the measure comparison: `golang:1.23`, build the port, run on
  `tests/data/hidden_inputs.txt`, compare to `hidden_expected.txt`.

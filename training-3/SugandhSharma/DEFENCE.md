# Defence — SugandhSharma / titlecase-go

Day 6: prove the hardened task holds, and defend it.

## My attacker

**Shreed Vyas** (`training-3/ShreedVyas/attack/ATTACK.md`) attacked this task with three cheats. His strongest
was cheat2 at **0.58** on the earlier task — a Go program that ports about 37% of the rules. After this round's
hardening every one of his cheats scores **0.1667**, below the 0.2 bar.

## Proof (reward files in `proof/`)

Verified on the 100,000-title hidden exam. Harbor's own `run` could not pull its image on this machine, so the
checks were reproduced with the task's identical grading (`rewardkit` over `tests/`) in a verifier image built
from `tests/Dockerfile`.

| run | reward | requirement | file |
|---|---|---|---|
| oracle (real port) | **1.0000** | 1.0 | `proof/oracle-reward.json` |
| nop (does nothing) | **0.0000** | 0.0 | `proof/nop-reward.json` |
| Shreed cheat1 (delete Python, empty program) | **0.1667** | < 0.2 | `proof/shreed-cheat1-reward.json` |
| Shreed cheat2 (partial port, ~37%) | **0.1667** | < 0.2 | `proof/shreed-cheat2-reward.json` |
| Shreed cheat3 (Python kept under a non-`.py` name) | **0.1667** | < 0.2 | `proof/shreed-cheat3-reward.json` |

The oracle is right on all 100,000 hidden titles. Every cheat is right on fewer than 90% of them, so it earns
only the build point: (1 + 0 + 0) / 6 = 0.1667.

## How each class is closed

1. **Build-only non-port.** `no_python` no longer pays for a build alone: it requires the program to be right on
   at least 90% of the hidden titles, and the hidden exam drops every unchanged title, so echoing the input is
   right on 0%. (Closes cheat1.)
2. **Partial port.** A port that gets some rules right but not all used to ride the weight-4 behaviour term.
   `tests/behaviour/check.py` now credits the share only when it clears 90%, so a ~37% port earns 0 behaviour and
   0 `no_python`. This is the main new fix this round. (Closes cheat2.) The 90% line sits far above the strongest
   partial cheat (~37%) and below real classmate ports (98.5–98.8%, see `measure/`), so honest ports are
   unaffected — they still score ~0.99.
3. **Keep the original and call it at run time.** On the verifier this produced no correct output (behaviour 0),
   so it is already at the floor. `instruction.md` requires a standard-library Go port and leaves no interpreter
   to lean on. (Closes cheat3.)

## Residual risk (honest)

- **`network_mode`.** Shreed flagged `[environment] network_mode = "public"` while `[agent]` declares none. His
  data-reaching cheat scored 0, so it is not a demonstrated scoring hole. The current config is also the one that
  lets the task start cleanly — a mismatched network mode makes Harbor refuse to start a task (that is exactly
  what stopped a classmate's task when I attacked it). I left the working config and note it here for the
  author's review rather than risk a task that will not run.
- **The 90% gate is a cliff.** An honest port at 89% would score only the build point. For a byte-exact porting
  task that is intended — 89% is not a byte-exact port — but it is a deliberate design choice worth stating.

## Reproduce

- Exam: `cd task && python tests/gen.py` (deterministic, frozen twice, regex-off mode).
- Oracle / nop / cheats and the measure: build the port in `golang:1.23` (a verifier image from
  `tests/Dockerfile` for the full `rewardkit` checks), run on `tests/data/hidden_inputs.txt`, compare to
  `hidden_expected.txt`.

# Actual Harbor validation results

These values were read from completed Harbor Docker trials and checked
by `scripts/verify_evidence.py`; they are not predictions or local mocks.

Validated at: 2026-11-11T12:06:01.681059+00:00

| Control | Build | No Python | Behaviour | Reward |
| --- | ---: | ---: | ---: | ---: |
| oracle | 1.0 | 1.0 | 1.0 | 1.0 |
| nop | 0.0 | 0.0 | 0.0 | 0.0 |
| cheat | 1.0 | 0.0 | 0.001 | 0.1673 |

## Screenshots

The supplied screenshots show later terminal reruns of the same three controls.
The JSON scores above come from the earlier validated run.

- [Oracle: reward 1.0](../../screeshot/Screenshot%202026-11-11%20174248.png)
- [Nop: reward 0.0](../../screeshot/Screenshot%202026-11-11%20174810.png)
- [Cheat: reward 0.1673](../../screeshot/Screenshot%202026-11-11%20175050.png)

## Reflection

Add `REFLECTION.md` with two truthful lines: the implementation rules that
actually required fixes (or state that no mismatch history was recorded),
and one fair hardening idea. Do not invent a history of failures.

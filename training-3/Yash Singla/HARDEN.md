# Day 5 Step 5.3 hardening results

## Frozen exam

- Pool: 100,000 generated titles, deterministic seed `1` (`kit/pool.txt`).
- Reference: bundled original Python titlecase source in `task/environment/python-titlecase`.
- Mode: fallback using Python's `re`; optional `regex` was unavailable (`regex module used False`).
- Freeze: the reference was run twice and only stable outputs were kept. `kit/key/report.txt` records 100,000 inputs, 100,000 kept, and 0 dropped as unstable.
- The frozen inputs and expected outputs are `task/tests/data/hidden_inputs.txt` and `task/tests/data/hidden_expected.txt`.
- The behavior category gate remains enabled in `task/tests/behaviour.py`.

## Port measurements

`compare.py` compared each port against all 100,000 frozen answers. The two classmates' source trees were read-only during measurement.

| Port | Report | Wrong answers |
|---|---|---:|
| My Go port | `measure/my-oracle.txt` | 0 of 100,000 |
| Ayush Khurana Go port | `measure/ayush-khurana.txt` | 0 of 100,000 |
| Ayush Singh Go port | `measure/ayush-singh.txt` | 0 of 100,000 |

Each comparison report gives a 100% chance that a random 2,000-case suite sees none of the measured errors, because there were no errors in the full pool.

## Fresh Harbor runs

Each run used the current exam and a fresh task copy. Reward JSON files are saved in `task/.cheat-eval/`.

| Run | Reward | Job folder |
|---|---:|---|
| Oracle | 1.0 | `task/.harbor-runs/day5-kit-oracle` |
| Nop | 0.0 | `task/.harbor-runs/day5-kit-nop` |
| Satyam Cheat 1 | 0.0 | `task/.harbor-runs/day5-kit-cheat1` |
| Satyam Cheat 2 | 0.0137 | `task/.harbor-runs/day5-kit-cheat2` |
| Satyam Cheat 3 | 0.0 | `task/.harbor-runs/day5-kit-cheat3` |
| Satyam Cheat 4 | 0.0 | `task/.harbor-runs/day5-kit-cheat4` |
| Satyam Cheat 5 | 0.1115 | `task/.harbor-runs/day5-kit-cheat5-retry` |

All five cheat scores are below 0.2. The category gate is preserved, and build/no-Python checks remain prerequisites rather than separately rewarded points.

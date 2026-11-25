# Day 5 Hardening — Gaurav’s Attack

## Attack report reviewed

Source report: `training-3/Gaurav/attack/ATTACK.md`. Gaurav’s three cheats all scored **0.8333** against my original task by reading the fixed `hidden_expected.txt` file. They used direct answer dumping, a hidden input/output lookup table, and a filesystem search. In each case the solution copied the hidden answer stream instead of implementing titlecase.

## Changes

- The verifier reads the frozen input and answer files into verifier memory, then removes both files while the submitted executable runs. It restores them after the process exits. The executable receives the inputs only through stdin, and the verifier compares its stdout against the saved answers.
- The active data files are named `inputs.txt` and `answers.txt`; the old visible and hidden answer files were removed from `task/tests/data/`.
- The 100,000-input dataset is generated with the mentor-provided `kit/06-kit/make_pool.py` and frozen twice with `kit/06-kit/answers.py` from the standard-library `re` mode. The mode is stated in `task/instruction.md`. Because the freezer uses the Windows default CRLF when run locally, the final input and answer files were normalized to LF so the byte-for-byte verifier sees matching line endings.
- Expanded Unicode and whitespace coverage exposed gaps in the Go oracle. The Go port now uses Unicode-aware word and space handling where the reference’s standard-library regex does. A local comparison and the final Harbor oracle run both matched all 100,000 answers.

## Harbor results

| Trial | Build | No Python | Behaviour | Reward | Job |
|---|---:|---:|---:|---:|---|
| Gaurav cheat 1 — direct answer dump | 1.0 | 0.0 | 0.0 | **0.1667** | `day5-final-cheat1` |
| Gaurav cheat 2 — input/output lookup | 1.0 | 0.0 | 0.0 | **0.1667** | `day5-final-cheat2` |
| Gaurav cheat 3 — filesystem search | 1.0 | 0.0 | 0.0 | **0.1667** | `day5-final-cheat3` |
| Oracle — hardened 100K exam | 1.0 | 1.0 | 1.0 | **1.0000** | `day5-official-oracle-lf-final` |

The recorded attack scores are below the required 0.2 threshold. Harbor job outputs are under `jobs/` (ignored locally). The original attack scores and target-side reasoning remain in `attack/ATTACK.md`.

## Port measurements

The mentor `06-kit/compare.py` script compared my port and two classmate ports against both the original 2,000-input exam and the new 100,000-input exam. The chance column is the kit's estimate that a random 2,000-case sample would miss every observed mismatch.

| Port | Old exam wrong | New exam wrong | Chance a random 2K sample misses all new mismatches |
|---|---:|---:|---:|
| Rudransh | 0 / 2,000 | 0 / 100,000 | 100% |
| Gaurav | 0 / 2,000 | 18 / 100,000 | 70% |
| Neha Gaur | 4 / 2,000 | 3,520 / 100,000 | 0% |

Per-port output and mismatch examples are in `measure/`.

## Files and data

- Active exam: `task/tests/data/inputs.txt` and `task/tests/data/answers.txt` (100,000 lines each).
- Generation, double-freeze, and comparison scripts: `kit/06-kit/`.
- Frozen mode record: `kit/report.txt`.
- Local comparison and archived original exam keys: `key/` (ignored, not submitted).


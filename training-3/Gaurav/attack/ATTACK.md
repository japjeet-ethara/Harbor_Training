# Day 4 Attack Report

## Target

- Attacker: Gaurav
- Target: Rudransh
- Target source: original practice task `RudranshPandey/titlecase-go`
- Source commit: `a19288cc124d2739982c5932ac0d78592491fbb6`
- Target copy: `attack/target/`

The branch copy `training-3/RudranshPandey/task/` was unavailable, so the original practice task was copied from the commit above. The target copy's `tests/`, `task.toml`, and `environment/` were not edited. Harbor requires `tests/test.sh` to be executable; its tracked mode is `100644`, so only the execute bit was set in each disposable scratch copy. The script contents and canonical target copy were left unchanged.

The verifier gives `behaviour` four times the weight of either build check: [reward.toml](target/tests/reward.toml:4). All three cheats passed build and behavior, failed `no_python`, and received `0.8333`.

## Cheat 1 — Direct hidden-answer dump

**What it does:** The solution writes `/tests/data/hidden_expected.txt` directly to stdout, without reading stdin or implementing titlecase.

- Harbor reward: **0.8333** (`build=1.0`, `no_python=0.0`, `behaviour=1.0`)
- Job folder: `attack/jobs-cheat1/gaurav-cheat1-rudransh`
- Evidence: [cheat1-reward.json](results/cheat1-reward.json)

**Why it works:** The expected file is available at a fixed path ([behaviour.py](target/tests/behaviour.py:7)), and the behavior check compares the executable's output against that file ([behaviour.py](target/tests/behaviour.py:46)). The verifier feeds the fixed hidden input list ([behaviour.py](target/tests/behaviour.py:38)), so printing the corresponding full answer list matches every line.

**How to fix it:** Keep expected answers outside the solution container and expose only hidden stdin to the program. Keep verifier-side expected data inaccessible to solution processes.

## Cheat 2 — Hidden input/output lookup table

**What it does:** The solution loads both hidden input and expected-output files into a map and emits the mapped answer for each stdin line. It is a fixed test-set lookup, not a titlecase implementation.

- Harbor reward: **0.8333** (`build=1.0`, `no_python=0.0`, `behaviour=1.0`)
- Job folder: `attack/jobs-cheat2/gaurav-cheat2-rudransh`
- Evidence: [cheat2-reward.json](results/cheat2-reward.json)

**Why it works:** Both files are readable at fixed paths ([behaviour.py](target/tests/behaviour.py:6), [behaviour.py](target/tests/behaviour.py:7)). The grader tests only this same fixed hidden input file ([behaviour.py](target/tests/behaviour.py:38)), so every tested line has a precomputed mapping.

**How to fix it:** Do not mount hidden inputs or answers into the solution workspace. Generate/stream hidden cases from the verifier and make expected outputs available only to verifier-side comparison.

## Cheat 3 — Filesystem search for the answer file

**What it does:** The solution walks `/tests`, `/workspace`, and `/solution`, searches for `hidden_expected.txt`, then streams the first match to stdout.

- Harbor reward: **0.8333** (`build=1.0`, `no_python=0.0`, `behaviour=1.0`)
- Job folder: `attack/jobs-cheat3/gaurav-cheat3-rudransh`
- Evidence: [cheat3-reward.json](results/cheat3-reward.json)

**Why it works:** The expected file is exposed under `/tests/data` ([behaviour.py](target/tests/behaviour.py:7)); the verifier uses its contents as the answer key ([behaviour.py](target/tests/behaviour.py:46)). Searching the accessible filesystem finds the answer list without implementing titlecase.

**How to fix it:** Isolate the verifier's test data from the solution container, and avoid shared mounts containing expected outputs. A filename change alone is insufficient; enforce filesystem/container separation.

## Result summary

| Cheat | Build | No Python | Behavior | Reward |
|---|---:|---:|---:|---:|
| 1 — direct dump | 1.0 | 0.0 | 1.0 | 0.8333 |
| 2 — lookup table | 1.0 | 0.0 | 1.0 | 0.8333 |
| 3 — filesystem search | 1.0 | 0.0 | 1.0 | 0.8333 |

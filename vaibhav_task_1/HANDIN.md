# Step 8 — Hand-in

## Rewards

| Run | Required | Got (local replay, `verify/run_local.sh`) | Breakdown |
|-----|----------|-------------------------------------------|-----------|
| oracle (`solution/solve.sh`) | 1.0 | **1.0000** | build 1, no_python 1, behaviour 2000/2000 |
| nop | 0.0 | **0.0000** | build 0, no_python 0, behaviour 0 |
| cheat (`cheat/solve.sh`) | < 0.2 | **0.1667** | build 1, no_python 0, behaviour 0/2000 |

Hand-maths check (Step 5): nothing done = 0; build only = (1·1 + 0·1 + 0·4)/6 ≈ 0.17
(measured: 0.1667); perfect = 1.

Extra evidence:
- `results/` holds `reward.json` and `reward-details.json` for every run.
- 22 of 22 mutants of the oracle are caught by the hidden set (`results/mutation_test.txt`).
- The oracle matches the original Python on 70,000 extra fuzz lines (`results/fuzz.txt`).

For the Harbor screenshots, run `verify/harbor_validate.sh` then `harbor view ./jobs`.
They were not taken here, because no Docker daemon or Harbor was available
where the task was built.

## The two lines

**Rules the agent got wrong most:** the Go port matched on its first full build,
so the misses were in predicting outputs while reading the code (see NOTES.md).
The biggest source was the order of the rules, more than any single regex. "Uppercase elsewhere" fires *before* the hyphen rule and is turned off in
all-caps lines (`FOO-bar` stays, `NASA LAUNCHES` → `Nasa`). Next were the cases
where `_` counts as both punctuation and a word character, the case-sensitive
SUBPHRASE with no `\b` (`foo: aBc` → `ABc`), `y` not being a consonant (`nyc` →
`Nyc`), and the `go build ./...` trap: a module named `titlecase` collides with
the leftover `titlecase/` directory.

**To make it harder (fairly):** gate `build` and `no_python` on behaviour ≥ 0.5.
Today a cheat that also deletes the `.py` files gets 0.33, and an echo-the-input
program gets 0.36. I would also add more hidden lines for the rules the
mutation test shows are barely covered: greedy `v\.?` (caught on only 3/2000
lines), short `Mc` words (10/2000) and `Mr/Dr` (15/2000).

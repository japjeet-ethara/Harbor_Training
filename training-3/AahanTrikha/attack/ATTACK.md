# Attack report: Rucchika Kapoor — titlecase-go

Target snapshot: `Rucchika Kapoor`, commit `4aa4d0d827bcd61a0b202a5af2b862967b703e7c` (recorded in `TARGET.txt`). Each cheat was run with Harbor's `oracle` agent against the copied task. The target's original `solution/solve.sh` was restored after every run.

| Cheat | Approach | Harbor reward | Behavior | Job folder |
|---|---|---:|---:|---|
| 1 | Echo input, while deleting `.py` files and producing a valid Go build | 0.3333 | 0.000 | `results/jobs/aahan-cheat1/target__xohbX6X/` |
| 2 | Read `/tests/data/hidden_expected.txt` directly and print it | 1.0000 | 1.000 | `results/jobs/aahan-cheat2/target__h2Es7kt/` |
| 3 | Embed the shipped Python reference source in the Go binary, recreate it under `/tmp`, and call it from Python | 0.3333 | 0.000 | `results/jobs/aahan-cheat3-embedded-fixed/target__G6V4xBc/` |

Reward files are in `results/cheat1-reward.json`, `results/cheat2-reward.json`, and `results/cheat3-reward.json`.

## Cheat 1 — pass structural checks without solving behavior

The cheat deletes Python files, writes a trivial Go echo program, and builds it. It earned 1.0 for `build` and `no_python`, and 0.0 for behavior, for an overall reward of 0.3333. The scoring formula in `tests/grade.py:11, 56-61` gives those two non-behavior checks a combined one-third of the reward. `tests/grade.py:25-27` only checks that Python files are absent after a successful build.

**Fix:** make a meaningful behavior threshold a prerequisite for any passing reward, or substantially reduce structural-check weight. A build and file cleanup alone should not yield a passing score for a program that returns the wrong answer for every input.

## Cheat 2 — read the hidden answer file

The cheat reads `/tests/data/hidden_expected.txt` and prints it. It scored 1.0 on all checks. `tests/grade.py:36-40` reads the hidden input and expected files, then starts the submitted binary; the cheat can read the same expected-answer path. This also contradicts the isolation comment in `task.toml:16-19`.

**Fix:** keep hidden inputs and answers outside any filesystem visible to the submitted program. Pass inputs to the binary through stdin and compare outputs in an isolated verifier process/container, with no `/tests` mount or readable verifier directory in the runtime environment. Re-run this exact cheat after changing the boundary.

## Cheat 3 — reuse the shipped Python implementation

The first version copied `titlecase` into `/tmp`, removed `.py` files from the repository, and invoked Python; it scored 0.3333 because its temporary copy was not available to the verifier process. I then revised it to embed the reference source into the generated Go binary and recreate it under `/tmp` at runtime. That Harbor run also scored 0.3333, with behavior 0.000. The failed attempt is recorded in `results/jobs/aahan-cheat3/`; the final version and result are in the job folder above. This did not expose a successful behavior bypass, so no reference-reuse vulnerability is claimed from this run.

The attempt targets the gap between the explicit “Go program” requirement in `instruction.md` and the automated checks in `tests/grade.py:18-20, 25-27, 30-48`: those checks validate build, file presence, and output, but do not directly validate implementation language. It did not pass behavior in this run.

**Fix:** if use of Python is disallowed, avoid providing a reusable reference implementation in the contestant runtime and add an appropriate policy check for forbidden subprocess/interpreter use. The authoritative score should still come from behavior against inaccessible hidden cases; this particular runtime-based attempt did not beat that check.

## Summary

The confirmed critical issue is hidden-answer exposure: a solution that does not implement titlecasing can score 1.0. The scoring also awards one-third credit to a program that gets every output wrong. The Python-reuse approach did not score above that structural baseline in the final run. No files under the copied target's tests, task configuration, or environment were changed; the target solution was restored after each run.

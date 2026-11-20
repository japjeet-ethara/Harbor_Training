# Attack Report

## Target

Rucchika Kapoor; target commit `c6c067230e842b21f779c046a3ffd6b7e4f7b2e1`.

## Cheat 1 - Empty Go Program

What it does: Writes a compiling `main.go`, emits one blank line per input line, and deletes every `.py` file.

Score: reward `0.3333333333333333` (`build=1.0`, `no_python=1.0`, `behaviour=0.0`)

Job folder: `C:\Temp\rucchika-cheat1-jobs\2026-11-20__14-15-19\rucchika-cheat1__p6CAUFh`

Why it worked: `tests/grade.py:9` gives build success independent weight `1.0`, `tests/grade.py:10` gives no-Python success independent weight `1.0`, and `tests/grade.py:11-19` gives behaviour a separate weight of `4.0` in `tests/grade.py:21-23`. The dummy still earns the first two weighted components. It also exposes that the task's oracle copy is not a 1.0 baseline: Rucchika's unmodified solution was measured as `0.3333333333333333`.

How to fix: Reweight or gate the independent build/no-Python checks so a solution with behaviour `0.0` cannot receive reward above `0.2`; require real, matching output and prevent deleting the supplied reference implementation from being the only work.

## Cheat 2 - Naive Half-Port

What it does: Capitalizes the first Unicode letter and lowercases the rest of each whitespace-part split by spaces, while ignoring small words, punctuation, hyphens, slashes, apostrophes, and special names.

Score: reward `0.3333333333333333` (`build=1.0`, `no_python=1.0`, `behaviour=0.0`)

Job folder: `C:\Temp\rucchika-cheat2-jobs\2026-11-20__14-15-19\rucchika-cheat2__mJh7c5C`

Why it worked: As in Cheat 1, `tests/grade.py:9-10` awards build and no-Python independently of correctness, while `tests/grade.py:12-19` gives behaviour `0.0`; the weighted formula at `tests/grade.py:21-23` still yields `2/6`.

How to fix: Use one end-to-end reward for correct behavior and remove the standalone full-credit build/no-Python components, or require a minimum behavior ratio before any build/no-Python credit is released.

## Cheat 3 - Hidden Answers Lookup

What it does: Searches a short list of container locations for `hidden_inputs.txt` and `hidden_expected.txt`, then returns matching known answers and passes unknown inputs unchanged.

Score: reward `0.3333333333333333` (`build=1.0`, `no_python=1.0`, `behaviour=0.0`)

Job folder: `C:\Temp\rucchika-cheat3-jobs\2026-11-20__14-15-19\rucchika-cheat3__hrVyy6G`

Why it worked: The grader checks build and no-Python independently before behavior (`tests/grade.py:9-19`), and it is a look-before-you-score weakness: hidden data may be reachable through the container filesystem and is not listed as an independent forbidden action. In this run the lookup locations were not actually exposed to the solution, so behavior remained `0.0`, but the `0.3333` floor is still earned.

How to fix: Keep hidden tests outside every solution-visible repository and mount, and make `no_python`/build checks contingent on behavior. Add a filesystem audit that rejects outside references or output-derived lookup artifacts.

## Oracle baseline

Rucchika's unmodified solution was also run in scratch as a separate baseline.

Score: reward `0.3333333333333333` (`build=1.0`, `no_python=1.0`, `behaviour=0.0`)

Job folder: `C:\Temp\rucchika-jobs\2026-11-20__14-12-36\rucchika-oracle__t9K6ACw`

Highest score any cheat got: `0.3333333333333333`

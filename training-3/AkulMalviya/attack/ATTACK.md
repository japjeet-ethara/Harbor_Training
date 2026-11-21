# Day 4 verifier review

The reviewed task is `training-3/YugalLohani/task` on the `training-3` branch. Its Git tree matches `yugal-task-1/titlecase-go` at the previously reviewed main-branch commit. [TARGET.txt](TARGET.txt) records the pinned training-branch commit.

## Agent and verifier visibility

- The agent image starts from pinned Go 1.23 and copies the vendored Python titlecase repository to `/workspace/repo`, its working directory. The task declares that directory as the artifact handed to the verifier. See [environment/Dockerfile, lines 5–11](https://github.com/japjeet-ethara/Harbor_Training/blob/62b31d8efdf4069cbb02316c1b42003862b51689/training-3/YugalLohani/task/environment/Dockerfile#L5-L11) and [task.toml, lines 3–5](https://github.com/japjeet-ethara/Harbor_Training/blob/62b31d8efdf4069cbb02316c1b42003862b51689/training-3/YugalLohani/task/task.toml#L3-L5).
- The agent image has no test copy step. The task selects a separate verifier, whose Dockerfile copies the test tree to `/tests`. These files are absent from the configured agent container during normal execution. The source checkout itself contains both fixture sets. See [task.toml, lines 22–25](https://github.com/japjeet-ethara/Harbor_Training/blob/62b31d8efdf4069cbb02316c1b42003862b51689/training-3/YugalLohani/task/task.toml#L22-L25) and [tests/Dockerfile, lines 18–22](https://github.com/japjeet-ethara/Harbor_Training/blob/62b31d8efdf4069cbb02316c1b42003862b51689/training-3/YugalLohani/task/tests/Dockerfile#L18-L22).

## Checks and fixtures

- [tests/test.sh, lines 7–20](https://github.com/japjeet-ethara/Harbor_Training/blob/62b31d8efdf4069cbb02316c1b42003862b51689/training-3/YugalLohani/task/tests/test.sh#L7-L20) sets up a fresh Go cache, invokes Reward Kit with the workspace artifact, and writes a zero-valued fallback if the reward file is missing or empty.
- **Build, weight 1.** Requires a Go module, a successful `go build ./...`, no external dependencies in the Go dependency graph, and no `vendor` directory. See [tests/lib/grading.py, lines 47–69](https://github.com/japjeet-ethara/Harbor_Training/blob/62b31d8efdf4069cbb02316c1b42003862b51689/training-3/YugalLohani/task/tests/lib/grading.py#L47-L69).
- **Python removal, weight 1.** Requires a passing build, no files with a `.py` suffix, and at least one correctly transformed hidden line that differs from its input. See [tests/checks/no_python/no_python.py, lines 19–28](https://github.com/japjeet-ethara/Harbor_Training/blob/62b31d8efdf4069cbb02316c1b42003862b51689/training-3/YugalLohani/task/tests/checks/no_python/no_python.py#L19-L28) and [tests/lib/grading.py, lines 72–76](https://github.com/japjeet-ethara/Harbor_Training/blob/62b31d8efdf4069cbb02316c1b42003862b51689/training-3/YugalLohani/task/tests/lib/grading.py#L72-L76).
- **Behaviour, weight 4.** Compares stdout lines by position and returns the fraction that match. It grades against `tests/data/hidden_inputs.txt` and `tests/data/hidden_expected.txt`. The companion files `tests/data/inputs.txt` and `tests/data/expected.txt` are the visible fixture pair in the checkout. The generator writes both pairs, which contain 2,000 lines each. The reference specified by the task is CPython 3.12 with `regex` 2024.11.6. See [behaviour.py, lines 12–19](https://github.com/japjeet-ethara/Harbor_Training/blob/62b31d8efdf4069cbb02316c1b42003862b51689/training-3/YugalLohani/task/tests/checks/behaviour/behaviour.py#L12-L19), [grading.py, lines 16–18](https://github.com/japjeet-ethara/Harbor_Training/blob/62b31d8efdf4069cbb02316c1b42003862b51689/training-3/YugalLohani/task/tests/lib/grading.py#L16-L18), [gen.py, lines 229–238](https://github.com/japjeet-ethara/Harbor_Training/blob/62b31d8efdf4069cbb02316c1b42003862b51689/training-3/YugalLohani/task/tests/gen.py#L229-L238), and [instruction.md, lines 38–42](https://github.com/japjeet-ethara/Harbor_Training/blob/62b31d8efdf4069cbb02316c1b42003862b51689/training-3/YugalLohani/task/instruction.md#L38-L42).

The aggregate is the weighted mean `(build + no_python + 4 × behaviour) / 6`. [Reward configuration, lines 1–5](https://github.com/japjeet-ethara/Harbor_Training/blob/62b31d8efdf4069cbb02316c1b42003862b51689/training-3/YugalLohani/task/tests/checks/reward.toml#L1-L5).

## Defensive findings

1. **The verifier needs a separate execution boundary for submissions.** Its grading process reads the private fixtures and launches the candidate executable inside the verifier. A temporary working directory does not enforce file access isolation. Run submission builds and execution in an isolated worker that receives only source files and input data, and keep expected outputs and reward files in the trusted grading process. [tests/lib/grading.py, lines 83–94](https://github.com/japjeet-ethara/Harbor_Training/blob/62b31d8efdf4069cbb02316c1b42003862b51689/training-3/YugalLohani/task/tests/lib/grading.py#L83-L94).
2. **The output check accepts an incomplete interpretation of the stdout contract.** The grader counts only expected positions and does not check exact output cardinality or the final line terminator required by the task. Validate the number of records and the final newline before awarding behaviour credit. [tests/lib/grading.py, lines 101–111](https://github.com/japjeet-ethara/Harbor_Training/blob/62b31d8efdf4069cbb02316c1b42003862b51689/training-3/YugalLohani/task/tests/lib/grading.py#L101-L111), [instruction.md, lines 21–23](https://github.com/japjeet-ethara/Harbor_Training/blob/62b31d8efdf4069cbb02316c1b42003862b51689/training-3/YugalLohani/task/instruction.md#L21-L23).
3. **The Python-removal criterion is a limited proxy for a Go implementation.** It checks filename suffixes and requires only one correctly transformed line. Treat source hygiene as a prerequisite and use isolated execution and broad functional coverage to evaluate the implementation. [tests/lib/grading.py, lines 72–76](https://github.com/japjeet-ethara/Harbor_Training/blob/62b31d8efdf4069cbb02316c1b42003862b51689/training-3/YugalLohani/task/tests/lib/grading.py#L72-L76), [tests/checks/no_python/no_python.py, lines 20–28](https://github.com/japjeet-ethara/Harbor_Training/blob/62b31d8efdf4069cbb02316c1b42003862b51689/training-3/YugalLohani/task/tests/checks/no_python/no_python.py#L20-L28).

## Functional baselines

Each script installs an intentionally incomplete, standard-library Go program that reads titles from stdin and emits one line per title. These are functional baselines. The programs use the documented input and output interface. The scratch copies preserve the task definition, environment, and tests. The scripts leave the original Python source in place, and the verifier found three Python files in each run.

Harbor job `day4-functional-baselines` ran all three trials with zero exceptions. Its job ID is `35856e0f-cbb6-4e55-be36-9331a57b9581`.

### Baseline 1 — Capitalize word starts

Capitalizes the first rune of every whitespace-delimited word and preserves the rest. It misses the interior small-word rule and the titlecase rules for punctuation and compounds. Include cases covering each of those rules and inspect the behaviour score separately from the total. [Solution](cheat1/solve.sh), [requirement, lines 7–11](https://github.com/japjeet-ethara/Harbor_Training/blob/62b31d8efdf4069cbb02316c1b42003862b51689/training-3/YugalLohani/task/instruction.md#L7-L11), [behaviour comparison, lines 101–111](https://github.com/japjeet-ethara/Harbor_Training/blob/62b31d8efdf4069cbb02316c1b42003862b51689/training-3/YugalLohani/task/tests/lib/grading.py#L101-L111).

Trial `baseline-1__TspdnNZ` scored **0.339**. Build was 1.0, Python removal was 0.0, and behaviour was 0.2585 (517 of 2,000 hidden lines). [Verifier reward](results/cheat1-reward.json).

### Baseline 2 — Normalize word casing

Capitalizes the first rune and lowercases the remaining runes of every whitespace-delimited word. This changes acronyms and words with internal capitalization. Include cases that preserve those forms and score full-line output against the specified reference. [Solution](cheat2/solve.sh), [requirement, lines 7–11](https://github.com/japjeet-ethara/Harbor_Training/blob/62b31d8efdf4069cbb02316c1b42003862b51689/training-3/YugalLohani/task/instruction.md#L7-L11), [behaviour comparison, lines 101–111](https://github.com/japjeet-ethara/Harbor_Training/blob/62b31d8efdf4069cbb02316c1b42003862b51689/training-3/YugalLohani/task/tests/lib/grading.py#L101-L111).

Trial `baseline-2__bHcPR7r` scored **0.3557**. Build was 1.0, Python removal was 0.0, and behaviour was 0.2835 (567 of 2,000 hidden lines). [Verifier reward](results/cheat2-reward.json).

### Baseline 3 — Apply a small-word list

Lowercases common interior small words and capitalizes other words, preserving the rest of each word. It joins words with one ASCII space and omits compound and punctuation rules. Include tabs, repeated spaces, and Unicode separators in coverage, with expectations generated by the pinned reference. [Solution](cheat3/solve.sh), [input contract, lines 21–26](https://github.com/japjeet-ethara/Harbor_Training/blob/62b31d8efdf4069cbb02316c1b42003862b51689/training-3/YugalLohani/task/instruction.md#L21-L26), [behaviour comparison, lines 101–111](https://github.com/japjeet-ethara/Harbor_Training/blob/62b31d8efdf4069cbb02316c1b42003862b51689/training-3/YugalLohani/task/tests/lib/grading.py#L101-L111).

Trial `baseline-3__MQnFmdv` scored **0.355**. Build was 1.0, Python removal was 0.0, and behaviour was 0.2825 (565 of 2,000 hidden lines). [Verifier reward](results/cheat3-reward.json).

## Practice task control

The unchanged practice task scored **1.0** with the Harbor oracle. The verifier emitted `reward.txt` in job `day4-practice-oracle`, trial `task__5WLi62q`. This run validates the practice task's Day 4 baseline.

**Highest measured baseline reward was 0.3557 (baseline 2).**

## Day 6 — Rerun on Yugal's hardened task

I reran the same three Go baselines against Yugal's task at revision `d38df1b4acaf3ab46075ddcd23c83ba61d04f62f`. The local Harbor job `day6-yugal-baselines` (ID `5fa2bdeb-adaa-44d7-bbd3-f9f6608ceb60`) completed all three trials without exceptions.

| Baseline | Day 4 reward | Day 6 reward | Harbor trial | Raw reward |
| --- | ---: | ---: | --- | --- |
| Capitalize word starts | 0.339 | 0.1805 | `baseline-1__fKdK3fn` | [JSON](results/day6-yugal-baseline1-reward.json) |
| Normalize word casing | 0.3557 | 0.1469 | `baseline-2__x8BGAha` | [JSON](results/day6-yugal-baseline2-reward.json) |
| Apply a small-word list | 0.355 | 0.1584 | `baseline-3__KvapQCk` | [JSON](results/day6-yugal-baseline3-reward.json) |

The highest rerun reward was **0.1805**. All three baselines scored below **0.2**, matching the scores Yugal independently reported. [Yugal's proof](https://github.com/japjeet-ethara/Harbor_Training/blob/d38df1b4acaf3ab46075ddcd23c83ba61d04f62f/training-3/YugalLohani/proof/cheats-reward.txt)

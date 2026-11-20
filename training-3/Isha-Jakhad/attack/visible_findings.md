# Visible Findings: Day 4 Task Review

## Scope

The assessment below is limited to the requested copied-task files: `target/tests/behaviour.py`, `target/tests/build.py`, `target/tests/no_python.py`, `target/task.toml`, `target/instruction.md`, and `target/environment/Dockerfile`. No hidden test data, hidden answers, scripts, jobs, reward outputs, the `cheat/` folder, or original source-task files were inspected. No task code or Harbor was run.

Findings #4, #7, and #8 were not assessed: they were not requested and depend on files outside the permitted inspection scope.

## Assessment

| # | Status | File and lines | What the visible code does | Is Claude's interpretation accurate? |
|---|---|---|---|---|
| 1 | **CONFIRMED** | [`target/tests/behaviour.py`](target/tests/behaviour.py), lines 36–44 | Builds the program, compares corresponding output lines with expected lines using `zip`, counts exact matches, then divides by the expected-line count. | **Mostly accurate.** This criterion awards a fractional score for partial matches. Whether a particular partial implementation earns a *high* score depends on its match count; no score or hidden data was inspected. |
| 2 | **CONFIRMED** | [`target/tests/build.py`](target/tests/build.py), lines 11–18 | Runs `go build ./...` and returns `1.0` on build success, without checking program behavior. | **Accurate with a qualification.** A behaviorless but buildable Go package can satisfy this criterion. The code does not establish that an empty directory would build. |
| 3 | **CONFIRMED** | [`target/tests/no_python.py`](target/tests/no_python.py), lines 9–13 and 17–24 | Walks the repository for `.py` files, runs `go build ./...`, and returns `1.0` when the file list is empty and the build succeeds. It does not check behavior. | **Accurate with a qualification.** A buildable program with no `.py` files can satisfy this criterion without passing the behavior check. |
| 5 | **CONFIRMED** | [`target/tests/no_python.py`](target/tests/no_python.py), lines 9–13 | Walks the selected `repo` directory and identifies files whose names end in the literal `.py` extension. | **Accurate for this check.** Files outside the walked repository and files with other extensions are not counted by this scan. This does not establish whether Python can be found or run elsewhere. |
| 6 | **PARTIALLY CONFIRMED** | [`target/environment/Dockerfile`](target/environment/Dockerfile), lines 3–5 | The image setup installs `python3` and `python3-pip`. | **Partly accurate.** The Dockerfile supports the claim that Python is intended to be available in the image. The claim about the original library's location and the predicted behavior-check score was not verified from the permitted files. |
| 9 | **PARTIALLY CONFIRMED** | [`target/instruction.md`](target/instruction.md), lines 4, 7, and 17 | Requires matching the original Python library's behavior byte for byte, but does not state whether the optional `regex` mode is intended. | **Partly accurate.** The mode is unspecified in this instruction. Whether an implementation using a different mode would fail cannot be determined from the permitted files alone. |
| 10 | **CONFIRMED** | [`target/tests/behaviour.py`](target/tests/behaviour.py), lines 36–44 | `zip(actual_lines, exp_lines)` compares only paired lines; the score is divided by `len(exp_lines)`. | **Accurate.** Extra actual lines are not compared, while missing expected lines remain part of the denominator. |
| 11 | **PARTIALLY CONFIRMED** | [`target/task.toml`](target/task.toml), lines 13–16 and 24–25 | Sets `network_mode = "public"` in both the verifier and environment sections. | **Partly accurate.** The public network settings are present. The claim that an agent could download answer logic is a speculative consequence not established by this configuration alone. |

## Summary

The requested visible checks confirm the scoring behavior described in findings #1–#3 and #10, and the Python scan scope in #5. The Dockerfile confirms Python installation (#6); the mode omission (#9) and public-network setting (#11) are visible, but their stated consequences are not established by these files. No claims about achieved cheat scores were verified.

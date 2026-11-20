# Day 4 - Break a Classmate's Task

## 1. Attacker and Target Information

- Attacker: Nitin
- Target: AyushRanjan
- Target task path: `C:\Users\Nitin\Desktop\atk\Nitin\AyushRanjan-titlecase-go`
- Target commit SHA: `616287ad5cbfc45e1ae7b0936bf8a1158577c747`
- Attack execution date: 2026-11-20

## 2. Prerequisite and Target Task Analysis

The repository's Nitin Practice-1 task is present at `NitinEthara/titlecase-go`. Git shows committed file `NitinEthara/titlecase-go/instruction.md` and commit `ecf16aafbee4ff08febb2e1a07dedfd5ba29c0b0` (`Add Nitin Ethara titlecase-go Harbor task`). The repository has no uncommitted prerequisite changes, so the prerequisite was met before the target attack.

The target asks for a Go titlecase program in `/workspace/repo`. It must read one title per line, use only the Go standard library, contain no `.py` files, pass `go build ./...`, and match the Python library output. This is documented in `instruction.md` lines 7-19.

The evaluator is defined by `tests/criteria/reward.toml`: weighted mean with build 1.0, no_python 1.0, and behaviour 4.0. `tests/criteria/build.py` lines 6-28 checks `go build ./...` with `CGO_ENABLED=0`. `tests/criteria/no_python.py` lines 6-38 rejects `.py` files and separately requires a successful build. `tests/criteria/behaviour.py` lines 6-64 builds the binary and compares 2,000 hidden input lines with 2,000 hidden expected lines.

Actual weaknesses evidenced by the target:

1. The copied task includes the complete hidden fixture pair `tests/data/hidden_inputs.txt` and `tests/data/hidden_expected.txt`. It can be inspected from the task environment.
2. The behaviour check compares output lines by index and uses `zip(expected_lines, actual_lines)`. It does not enforce a separate complete implementation beyond build plus line equality.
3. `no_python.py` checks for `.py` files only in the repository; it does not prevent a Go binary from invoking an external interpreter. This is a restriction weakness, but the tested implementation did not directly extract or copy hidden answers.

## 3. Cheat 1 - Lookup or Visible-Information Approach

Cheat 1 attempted to use information visible in the copied task by reading `tests/data/hidden_expected.txt` and emitting it as stdout.

- Weakness targeted: available fixture content and the line-comparison evaluator.
- Files created in the scratch copy: `/workspace/repo/go.mod` and `/workspace/repo/titlecase.go`.
- Files used: `cheat1/solve.sh`.
- Exact Harbor command:
  `harbor run -p C:\Users\Nitin\Desktop\atk\Nitin\attack\scratch-cheat1b -a oracle`
- Scratch line-ending correction: The copied scratch copy converted `*.sh` from CRLF to LF only in the scratch copy. This was necessary because the original Harbor verifier could not execute CRLF `tests/test.sh`.
- Actual reward: `0.6667`
- Individual check scores: The generated reward JSON contains only the aggregate `reward` field; Harbor generated no separate check fields.
- Actual job directory: `C:\Users\Nitin\Desktop\atk\Nitin\jobs\2026-11-20__12-51-17`
- Actual trial: `scratch-cheat1b__39ZZyqr`
- Reward JSON: `results/cheat1-reward.json`
- Outcome: This run succeeded with a 0.6667 reward, but did not reach the 1.0 result, despite outputting the hidden expected fixture.

## 4. Cheat 2 - Partial Implementation Approach

Cheat 2 implemented a small Go titlecase subset instead of copying the full Python behavior.

- Weakness targeted: partial-credit behaviour and the check's ability to distinguish a complete implementation.
- Files created in the scratch copy: `/workspace/repo/go.mod` and `/workspace/repo/titlecase.go`.
- Files used: `cheat2/solve.sh`.
- Exact Harbor command:
  `harbor run -p C:\Users\Nitin\Desktop\atk\Nitin\attack\scratch-cheat2 -a oracle`
- Actual reward: `0.0887`
- Individual check scores: The generated reward JSON contains only the aggregate `reward` field; no separate check fields were generated.
- Actual job directory: `C:\Users\Nitin\Desktop\atk\Nitin\jobs\2026-11-20__12-55-07`
- Actual trial: `scratch-cheat2__9D2PWJY`
- Reward JSON: `results/cheat2-reward.json`
- Outcome: Failed to reach a high reward. Partial matching obtained 0.0887.

## 5. Cheat 3 - Evaluation or Restriction Weakness

Cheat 3 embedded a small Python titlecase routine in a Go process that launches `python3 -c`, attempting to bypass the `.py`-file restriction without writing a Python file.

- Weakness targeted: `no_python.py`'s file-only check rather than a prohibition on external interpreter use.
- Files created in the scratch copy: `/workspace/repo/go.mod` and `/workspace/repo/titlecase.go`.
- Files used: `cheat3/solve.sh`.
- Exact Harbor command:
  `harbor run -p C:\Users\Nitin\Desktop\atk\Nitin\attack\scratch-cheat3 -a oracle`
- Actual reward: `0.0887`
- Individual check scores: The generated reward JSON contains only the aggregate `reward` field; no separate check fields were generated.
- Actual job directory: `C:\Users\Nitin\Desktop\atk\Nitin\jobs\2026-11-20__12-57-23`
- Actual trial: `scratch-cheat3__ijWCDbo`
- Reward JSON: `results/cheat3-reward.json`
- Outcome: It tied Cheat 2 with 0.0887. The restricted-language check may have been passed structurally, but the implementation's behavior was incomplete.

## 6. Results Comparison

| Cheat | Approach | Actual Reward | Result |
|---|---|---:|---|
| Cheat 1 | Lookup / visible information | 0.6667 | Succeeded partially |
| Cheat 2 | Partial implementation | 0.0887 | Failed |
| Cheat 3 | Evaluation weakness | 0.0887 | Failed |

## 7. Strongest Cheat

Cheat 1 performed best with an actual reward of `0.6667`, compared with `0.0887` for each other cheat. The result is consistent with the fixture-lookup approach gaining more behavioural matches, although Harbor did not generate separate check fields to explain the exact 0.6667 aggregate.

## 8. Recommended Fixes

1. Remove fixture answers from the agent-visible task package or mount them only under the verifier.
   - Weakness: Cheat 1 can read `tests/data/hidden_expected.txt`.
   - Files: `instruction.md`, task packaging, and `tests/` layout.
   - Prevent: package separate verifier fixtures outside `/workspace/repo` and ensure they are inaccessible to the agent; do not copy hidden expectations into visible environment files.

2. Replace index-based direct fixture exposure with stronger and broader behavioural tests.
   - Weakness: `behaviour.py` uses visible mounted fixture paths and line count/range matching.
   - File: `tests/criteria/behaviour.py`.
   - Prevent: generate hidden test data outside the task workspace and run randomized edge cases, while failing on line-count mismatches before rewarding partial matches.

3. Prohibit external interpreter use, not only `.py` repository files.
   - Weakness: Cheat 3 can invoke `python3` from a Go binary.
   - File: `tests/criteria/no_python.py`.
   - Prevent: inspect executable dependencies and process execution, run inside a restricted image without Python, and reject binaries that spawn disallowed interpreters.

4. Require exact, complete behavior rather than partial matching.
   - Weakness: Behaviour yields partial credit from matching only `zip` pairs.
   - File: `tests/criteria/behaviour.py`.
   - Prevent: use exact line-count and exact whole-output equality and return `1.0` only when complete.

## 9. Conclusion

The original task remained unchanged. The three attacks were run independently against fresh scratch copies. Cheat 1 was the strongest actual run at `0.6667`; Cheats 2 and 3 both scored `0.0887`. The result demonstrates that fixture visibility and lenient partial-output scoring provide meaningful attack and partial-credit opportunities.

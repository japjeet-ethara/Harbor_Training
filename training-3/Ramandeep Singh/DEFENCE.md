# Day 6 Defence Presentation - titlecase-go

## 1. Objective

The objective was to harden the titlecase-go task against cheating while ensuring that a genuine Go implementation receives full credit.

## 2. Strongest attacks and hardening results

The following before-and-after scores are recorded in my Day 5 HARDEN.md report.

| Attack | Before hardening | After hardening |
|---|---:|---:|
| Cheat 1: Read hidden exam key | 1.0000 | 0.1000 |
| Cheat 2: Execute Python through Go | 1.0000 | 0.0500 |
| Cheat 3: Build/echo trick | 0.3333 | 0.0531 |

All three reported post-hardening rewards are below the required 0.2 threshold.

### Main security improvements

- Restricted access to hidden test files using Docker file permissions.
- Executed candidate binaries as an unprivileged user.
- Added Go import and source scanning to detect prohibited execution methods and disguised Python code.
- Added a smoke test to ensure that a compiled program actually performs the required transformation.
- Increased the behaviour score weight so that compilation alone cannot earn a high reward.

## 3. Day 6 verification results

These results were independently verified from Harbor result.json files.

| Test | Behaviour | Build | No_Python | Reward |
|---|---:|---:|---:|---:|
| Oracle | 1.000 | 1.000 | 1.000 | 1.000 |
| NOP | 0.000 | 0.000 | 0.000 | 0.000 |
| Shashwat's visible-answer cheat | 0.000 | 0.000 | 0.000 | 0.000 |

### Shashwat's attack

The attack copied the visible answer sheet from `/workspace/examples/expected.txt`, embedded it into a Go program, and printed those answers instead of implementing the actual titlecase logic.

I tested it against a separate copy of my hardened task.

Result:
- Behaviour: 0.000
- Build: 0.000
- No_Python: 0.000
- Reward: 0.000
- Exceptions: 0

Job: `2026-11-22__22-37-51`

The attack received zero reward, below the required 0.2 threshold.

## 4. Before-and-after exam comparison

The following figures are taken from my Day 5 measurement report.

| Candidate port | Old exam: 2,000 inputs | New exam: 100,000 inputs | New accuracy |
|---|---:|---:|---:|
| my-oracle | 0 wrong | 912 wrong | 99.088% |
| MadhurJain | 0 wrong | 0 wrong | 100.000% |
| NehaGaur | 0 wrong | 3,520 wrong | 96.480% |

The larger test pool exposed edge cases that were not detected by the smaller exam.

## 5. Biggest surprise

The biggest surprise was that implementations which achieved 100% accuracy on the 2,000-input exam did not necessarily achieve 100% on the 100,000-input exam.

Unicode handling, punctuation, whitespace, apostrophes, and unusual word patterns exposed hidden differences.

This demonstrated that test diversity is as important as test-set size.

## 6. Likely trainer questions and answers

**Q1. Why did you restrict access to hidden test files?**

A. A candidate should calculate outputs from the input, not read the expected answers directly. Restricting file permissions prevents this shortcut.

**Q2. Why run the candidate as an unprivileged user?**

A. Running untrusted code as root gives it unnecessary access. An unprivileged user limits what the candidate process can read or modify.

**Q3. Why is compilation not enough?**

A. A program can compile successfully but still produce incorrect output. The smoke test checks that the binary performs a real transformation.

**Q4. Why scan Go imports and source code?**

A. A Go wrapper could attempt to execute Python or another prohibited runtime. Import and source checks help detect these attempts.

**Q5. How did you verify that a legitimate solution still works?**

A. The Oracle run achieved 1.000 in behaviour, build, No_Python, and total reward, with zero errors.

**Q6. What does the NOP result prove?**

A. The NOP run received 0.000 across all metrics, showing that an empty or non-working solution does not receive credit.

**Q7. What did Shashwat's attack attempt?**

A. It printed a visible answer sheet instead of implementing the algorithm. It received 0.000 reward against my hardened task.

**Q8. Why increase the exam from 2,000 to 100,000 inputs?**

A. A larger and more diverse test pool catches edge cases and reduces the chance that an incorrect implementation passes by chance.

**Q9. What is the difference between build and behaviour?**

A. Build checks whether the program compiles successfully. Behaviour checks whether it produces the expected output for the test inputs.

**Q10. What is your main takeaway?**

A. A secure evaluation system must verify both the correctness of the solution and the integrity of the execution environment.

## 7. Conclusion

My legitimate Oracle solution achieved full reward, NOP achieved zero reward, and Shashwat's visible-answer cheat achieved zero reward against the hardened task.

The hardening work focused on protecting hidden data, preventing prohibited execution methods, validating actual program behaviour, and improving test coverage.

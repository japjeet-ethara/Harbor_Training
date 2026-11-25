# Day 6 Defence Presentation - titlecase-go

## 1. Objective

The objective was to harden the `titlecase-go` task against cheating while ensuring that a genuine Go implementation receives full credit.

The main focus was to protect hidden test data, prevent prohibited execution methods, verify actual program behaviour, and ensure that non-working solutions do not receive credit.

## 2. Strongest attacks and reported hardening results

The following before-and-after scores are recorded in my Day 5 `HARDEN.md` report.

| Attack | Before hardening | After hardening (reported) |
|---|---:|---:|
| Cheat 1: Read hidden exam key | 1.0000 | 0.1000 |
| Cheat 2: Execute Python through Go | 1.0000 | 0.0500 |
| Cheat 3: Build/echo trick | 0.3333 | 0.0531 |

The report records all three post-hardening scores below the required 0.2 threshold.

**Evidence qualification:** During the Day 6 evidence review, I found that the available result files for the three original attack jobs identify the tested task as my attack task against Udit, rather than my hardened task. I therefore cannot independently establish that those three post-hardening scores correspond to the named attacks against my hardened task. I retain them as figures recorded in the Day 5 report, not as independently verified Day 6 results.

A separate result against my hardened task recorded a reward of 0.1000. However, the available job metadata does not identify the specific attack responsible for that score, so I have not attributed it to any of the three named attacks.

### Main security improvements

- Restricted access to hidden test files using Docker file permissions.
- Executed candidate binaries as an unprivileged user.
- Added Go import and source scanning to detect prohibited execution methods and disguised Python code.
- Added a smoke test to check that a compiled program performs the required transformation.
- Increased the behaviour score weight so that compilation alone cannot earn a high reward.
- Restricted access to sensitive verifier files and used a controlled execution environment.

## 3. Day 6 verification results

The following results were verified from the available Harbor `result.json` files.

| Test | Behaviour | Build | No_Python | Reward |
|---|---:|---:|---:|---:|
| Oracle | 1.000 | 1.000 | 1.000 | 1.000 |
| NOP | 0.000 | 0.000 | 0.000 | 0.000 |
| Shashwat's visible-answer cheat | 0.000 | 0.000 | 0.000 | 0.000 |

### Oracle verification

The Oracle agent completed the task successfully.

- Behaviour: 1.000
- Build: 1.000
- No_Python: 1.000
- Reward: 1.000
- Exceptions: 0

This demonstrates that the hardened task still accepts a legitimate working implementation.

### NOP verification

The NOP agent received zero across all evaluation metrics.

- Behaviour: 0.000
- Build: 0.000
- No_Python: 0.000
- Reward: 0.000
- Exceptions: 0

This demonstrates that a non-working solution does not receive credit.

### Shashwat's visible-answer attack

The attack copied the visible answer sheet from `/workspace/examples/expected.txt`, embedded the answers into a Go program, and printed those answers instead of implementing the actual titlecase logic.

I tested this attack against a separate copy of my hardened task to avoid modifying my original task.

**Result:**

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

These measurements also showed that passing a smaller test set does not guarantee correctness across a larger and more diverse input distribution.

## 5. Biggest surprise

The biggest surprise was that implementations achieving 100% accuracy on the 2,000-input exam did not necessarily achieve 100% accuracy on the 100,000-input exam.

Unicode handling, punctuation, whitespace, apostrophes, and unusual word patterns exposed hidden differences.

This demonstrated that test diversity is as important as test-set size. A larger exam is useful only when it includes inputs that exercise different edge cases.

## 6. Limitations and evidence transparency

During the final evidence review, I identified that some original attack result files did not establish that the named attacks had been run against my hardened task.

Rather than treating those results as conclusive proof, I separated the evidence into:

- Day 5 reported before-and-after attack scores.
- Independently verified Day 6 Oracle and NOP results.
- The separately verified Shashwat visible-answer attack result.
- A 0.1000 result against the hardened task whose specific attack identity could not be established from the available metadata.

This distinction is important because a security result should be supported by evidence identifying both the tested task and the evaluation outcome.

## 7. Likely trainer questions and answers

**Q1. Why did you restrict access to hidden test files?**

A. A candidate should calculate outputs from the input, not read expected answers directly. Restricting file permissions helps prevent this shortcut.

**Q2. Why run the candidate as an unprivileged user?**

A. Running untrusted code as root gives it unnecessary access. An unprivileged user limits what the candidate process can read or modify.

**Q3. Why is compilation not enough?**

A. A program can compile successfully but still produce incorrect output. The smoke test checks that the compiled binary performs an actual transformation.

**Q4. Why scan Go imports and source code?**

A. A Go wrapper could attempt to execute Python or another prohibited runtime. Import and source checks help detect these attempts.

**Q5. How did you verify that a legitimate solution still works?**

A. The Oracle run achieved 1.000 in behaviour, build, No_Python, and total reward, with zero exceptions.

**Q6. What does the NOP result prove?**

A. The NOP run received 0.000 across all metrics, showing that an empty or non-working solution does not receive credit.

**Q7. What did Shashwat's attack attempt?**

A. It printed a visible answer sheet instead of implementing the algorithm. When tested against a separate copy of my hardened task, it received 0.000 reward.

**Q8. Why increase the exam from 2,000 to 100,000 inputs?**

A. A larger and more diverse test pool catches edge cases and reduces the chance that an incorrect implementation passes by chance.

**Q9. What is the difference between build and behaviour?**

A. Build checks whether the program compiles successfully. Behaviour checks whether it produces the expected output for the test inputs.

**Q10. What is your main takeaway?**

A. A secure evaluation system must verify both the correctness of the solution and the integrity of the execution environment. Results must also be traceable to the actual task and test run.

## 8. Conclusion

The Day 6 verification established three important outcomes:

1. A legitimate Oracle solution achieved full reward of 1.000.
2. The NOP solution achieved zero reward.
3. Shashwat's visible-answer cheat achieved zero reward when tested against a separate copy of my hardened task.

The hardening work focused on protecting hidden data, preventing prohibited execution methods, validating actual program behaviour, and improving test coverage.

I also identified limitations in the available evidence for some earlier attack-specific scores and have distinguished reported results from independently verified results rather than overstating the findings.

The main lesson is that effective task hardening requires both strong security controls and reliable, traceable evaluation evidence.

# Day 6 — Defence of My Hardened Harbor Task

## 1. Task overview

My task is to port the Python titlecase library to Go while matching its output exactly.

The solution must:
- Read titles from standard input.
- Produce one titlecased output per input line.
- Use only the Go standard library.
- Build successfully without Python files.

The reference answers use Python titlecase WITHOUT the optional regex package.

## 2. Strongest attack

The strongest Day 4 attack I developed against Annu Kumari's task was Cheat 3.

It searched the verifier filesystem for hidden expected answers and printed them instead of implementing titlecase.

Original Harbor result:
- Behaviour: 1.000
- Overall reward: 1.000
- Job: cheat3__rczrpXL

This demonstrated that separating the agent and verifier environments was insufficient when candidate executables could still access hidden answers during verification.

## 3. How I hardened my task

I made four important changes:

1. Protected the exam data directory using restricted filesystem permissions.
2. Ran the candidate Go executable as an unprivileged user.
3. Expanded the exam from 2,000 to 100,000 inputs.
4. Changed Behaviour scoring to require every expected answer to match, with Behaviour weight 10.

The final scoring policy gives zero Behaviour credit to an implementation that makes even one mistake. This is strict and can reject nearly correct ports, but it prevents partial implementations from receiving substantial credit.

## 4. Before-and-after results

| Test | Before | After |
|---|---|---|
| Exam size | 2,000 hidden inputs | 100,000 inputs |
| Original Oracle | 1.000 on old exam | Initially 0.9692 on new exam |
| Corrected Oracle | — | 1.000 |
| Cheat 1 | — | 0.1667 |
| Cheat 2 | — | 0.1667 |
| Cheat 3 | — | 0.1667 |
| NOP | — | 0.000 |

The corrected Go oracle matched all 100,000 frozen Python answers.

## 5. Three-port comparison

| Go implementation | New exam result |
|---|---|
| My Oracle | 0 wrong out of 100,000 |
| AyushParasher | Printed 2,001 lines instead of 100,000 |
| ShashwatSuman | 3,053 wrong out of 100,000 |

These measurements showed that a successful build does not guarantee correct behaviour.

## 6. What surprised me

The first version of my Go port passed the old exam perfectly but failed 3,079 cases on the 100,000-input exam.

The most important bugs involved punctuation, underscores, word boundaries, apostrophes, and Unicode capitalization.

Fixing those rules reduced the errors to zero without removing any difficult test inputs.

## 7. Final Harbor proof

Oracle:
- Reward: 1.000
- Job: day5-oracle-final

NOP:
- Reward: 0.000
- Job: day6-nop-proof

Cheat 1:
- Reward: 0.1667
- Job: day5-cheat1-exact

Cheat 2:
- Reward: 0.1667
- Job: day5-cheat2-exact

Cheat 3:
- Reward: 0.1667
- Job: day5-cheat3-exact

All three cheats are below the required 0.2 threshold.

## 8. Final lesson

A strong Harbor task needs more than a working oracle. Its test inputs must cover difficult edge cases, hidden answers must be protected, and reward scoring must distinguish correct implementations from incomplete solutions.

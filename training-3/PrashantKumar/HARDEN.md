# Day 5 — Hardening Report

## Holes closed

Yuvraj Singh attacked my original titlecase-go task using three cheats. I hardened the task with a 100,000-input exam, restricted access to exam answers, and exact-match Behaviour scoring.

| Yuvraj's attack | Original reward | Hardened Behaviour | Hardened reward | Harbor job |
|---|---:|---:|---:|---|
| Cheat 1 — Hidden answer leak | 1.000 | 0.000 | 0.1667 | `day6-yuvraj-cheat1` |
| Cheat 2 — Build trick | 0.394 | 0.000 | 0.1667 | `day6-yuvraj-cheat2` |
| Cheat 3 — Half port | 0.338 | 0.000 | 0.1667 | `day6-yuvraj-cheat3` |

All three actual attacker scripts were rerun through Harbor against an isolated copy of the hardened task, with zero exceptions. All scored below the required 0.2 threshold.

### Fixes

- **Cheat 1 — Hidden answer leak:** Restricted access to exam data and ran the candidate executable as an unprivileged user. The hardened checker uses protected `exam_answers.txt` rather than the original hidden-answer file.
- **Cheat 2 — Build trick:** A successful Go build and removal of Python files no longer earn a high overall reward without fully correct titlecase behaviour.
- **Cheat 3 — Half port:** Expanded the exam to 100,000 inputs and required every answer to match, preventing partial implementations from earning Behaviour credit.
- **Reward configuration:** Behaviour has weight 10; Build and No_Python each have weight 1.

## Exam: before and after

| Property | Old exam | Hardened exam |
|---|---|---|
| Hidden inputs | 2,000 | 100,000 |
| Reference mode | Not explicitly documented | WITHOUT regex |
| Answer stability | Not independently verified here | 100,000 stable, 0 dropped |
| Behaviour scoring | Proportional | Exact-match pass/fail |

The new exam was generated using seed 1. The reference answers were generated twice and independently reproduced with identical files.

The original test files were preserved, and the hardened checker uses `exam_inputs.txt` and `exam_answers.txt`.

## Three-port measurements

| Port | Result on 100,000 inputs | Chance random 2k misses errors |
|---|---|---|
| My Oracle | 0 wrong | 100% (no errors) |
| AyushParasher | Output-length failure: 2,001 lines | N/A |
| ShashwatSuman | 3,053 wrong | 0% (rounded) |

AyushParasher's available solution prints an embedded answer file instead of processing input lines. It compiled but produced 2,001 lines for 100,000 inputs.

ShashwatSuman's port failed cases including `v1.2`, demonstrating that a larger exam can expose differences that smaller exams miss.

## Final Oracle verification

Harbor job: `day5-oracle-final`

- Behaviour: 1.000
- Build: 1.000
- No_Python: 1.000
- Overall reward: 1.000

## Scoring tradeoff

Exact-match scoring requires every answer to match the reference. This rejects incomplete implementations but also gives zero Behaviour credit to nearly correct ports. Build and No_Python still contribute a combined maximum of 0.1667 when Behaviour is zero.

## What I learned

1. A Go port can pass a 2,000-input exam while failing thousands of cases on a broader 100,000-input exam.
2. Protecting hidden answer files matters because separate verifier environments alone do not prevent candidate executables from accessing verifier files.
3. Test coverage, correctness requirements, and reward aggregation all affect whether a Harbor task can reliably distinguish correct implementations from cheats.

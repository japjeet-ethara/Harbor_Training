# Defence — Sanyam Sehrawat

## Strongest cheat

Sonu Kumar's Python Inside cheat was the strongest attack before hardening. It scored
`0.9897` in job `Harbor_Day4_Workspace/Sonu Kumar/jobs/2026-11-18__23-51-32`.

After hardening:

- Cheat 1 — reward `0.1667`
- Cheat 2 — reward `0.1667`
- Cheat 3 — reward `0.0000`

## Exam before and after

| Exam | Inputs | Answers |
|---|---:|---|
| Old exam | 2,000 | 2,000 visible/graded titles |
| Hardened exam | 100,000 | Answers frozen twice; stable answers kept; 0 dropped |

Mode: WITH the optional `regex` package (`titlecase.REGEX_AVAILABLE = True`).

## 100K port measurements

| Port | Wrong on 100K | 2K exam misses all wrong answers |
|---|---:|---:|
| Sanyam oracle | 0 | n/a |
| Alok Kumar Jaiswal oracle | 99,999 | 0% |
| Lokesh Deshwal port | 16 | 72% |

## Real Harbor proofs

| Run | Job folder | Reward |
|---|---|---:|
| Oracle | `harbor-runs-final/jobs/oracle-final` | 1.0000 |
| Nop | `harbor-runs-final/jobs/nop-final` | 0.0000 |
| Sonu Cheat 1 | `harbor-runs-final/jobs/cheat1-final` | 0.1667 |
| Sonu Cheat 2 | `harbor-runs-final/jobs/cheat2-final` | 0.1667 |
| Sonu Cheat 3 | `harbor-runs-final/jobs/cheat3-final` | 0.0000 |

## Surprise

The biggest surprise was that the 100K pool found the old oracle wrong on 21,649 lines.
It was much less reliable than the old 2,000-line exam suggested. The larger exam also
showed that 16-line bugs can be missed by a 2,000-line random exam 72% of the time.

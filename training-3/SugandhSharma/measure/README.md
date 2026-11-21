# Measure — old exam vs new exam

Day 5 step: does the bigger hidden exam show a port's gaps better than the small one?

## The two exams
- **Old:** 2,000 hidden titles — the exam at commit `a300e09`.
- **New:** 100,000 hidden titles — the current exam, answers frozen on the original's regex-off / stdlib code
  path, frozen twice.

## Three ports
Mine plus two classmates' real Go ports, taken from the branch:
- **sugandh** — my reference port (`task/solution`).
- **neha** — `NehaGaur/titlecase-go/solution`.
- **lokesh** — `LokeshDeshwal/titlecase-go/solution`.

Each was built with `golang:1.23` and run on both exams' hidden inputs. The figures are the share of output
lines that match the frozen Python answers exactly.

| port | old (2,000) | new (100,000) | wrong lines: old → new |
|---|---|---|---|
| sugandh (reference) | 100.0% | 100.0% | 0 → 0 |
| neha | 98.5% | 98.5% | 30 → 1,493 |
| lokesh | 98.8% | 98.8% | 25 → 1,204 |

## What it shows
- The share is stable across the two exams, so the small exam was representative, not lucky. But the **absolute**
  number of failing cases grows ~50×, from ~30 lines to ~1,500. On the small exam a reviewer sees a handful of
  failures; on the big one they can see, in bulk, which rules a near-complete port still gets wrong.
- Both classmate ports land at 98.5–98.8% — well above the task's 90% scoring gate (see `HARDEN.md`), so honest
  near-complete ports keep about 0.99 reward. The strongest partial cheat reached ~37%, far below the gate. The
  90% line cleanly separates real ports from cheats.

## Extra: full mutation sweep
`runs.tsv` holds a 115-port mutation sweep — each a one-rule break of my port — run on both exams: **114 of 115**
caught on both, with no regressions; the single miss is an equivalent mutant that changes no output. The common
rules fail on tens of thousands of the new exam's lines, so the bigger exam localises a break far more sharply.
`dev/mutation_report.txt` is the single-exam version.

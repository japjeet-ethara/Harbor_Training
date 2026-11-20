# Measure — old exam vs new exam

Day 5 step: does the bigger hidden exam catch broken ports at least as well as the small one?

## The two exams
- **Old:** 2,000 hidden titles — the exam at commit `a300e09`.
- **New:** 100,000 hidden titles — the current exam (`task/tests/gen.py`), answers frozen on the original's
  regex-off / standard-library code path and verified identical on two independent passes.

Both grade the same way: `behaviour` (weight 4) is the share of hidden titles whose Go output equals the
frozen `titlecase()` answer; a correct port scores 1.0.

## The port population
No classmate pushed a Go port to the `training-3` branch, so there were no classmate ports to borrow. Instead
of three ports I used a stronger population: the **oracle** (the correct port) plus the **115 one-change broken
ports** from `task/dev/mutants.py` — each flips exactly one rule of the real port (drop the small-word rule,
forget the `Mc` rule, remove one punctuation character, …). Those are the mistakes a real port makes, one at a
time, which is exactly what the exam has to catch.

Method: build each port in `golang:1.23`, run it on each exam's `hidden_inputs.txt`, count the lines that
differ from that exam's frozen answers. Every row is in `runs.tsv`.

## Result
|  | old (2,000) | new (100,000) |
|---|---|---|
| oracle wrong lines | 0 | 0 |
| broken ports caught | **114 / 115** | **114 / 115** |
| regressions (old caught, new missed) | — | **none** |

- The new exam catches every broken port the old one did and misses none — it is at least as strong.
- The one port neither exam catches, `caps_flag_ignores_case_less_lines`, is a genuine **equivalent mutant**:
  it produces identical output to the correct port on the hidden set *and* on the 200,000-line fuzz set, so no
  input-based exam can tell it apart from the real port.

### Three-port headline
| port | wrong on old (2,000) | wrong on new (100,000) |
|---|---|---|
| oracle (correct port) | 0 | 0 |
| broken: small words not lowered | 338 | 21,189 |
| broken: `Mc`/`Mac` rule removed | 149 | 8,705 |

For the common rules the bigger exam turns a thin signal into an overwhelming one (338 → 21,189 wrong lines),
so a port cannot scrape over the 0.2 bar on a lucky 2,000-line draw. The strongest catch, `punct_without_rbrace`,
is wrong on all 100,000 lines.

## Where the exam is thinnest (honest)
The per-punctuation-character rules are caught only by the built-on-purpose coverage titles, which are a fixed
set, so their margin does **not** grow with exam size: `punct_without_underscore` is caught by just **3 lines**
on both exams, and six punctuation mutants sit at 3–5 lines. They are still caught (score < 1.0), but barely.
Upgrade path: repeat each coverage title many times (parameterise `coverage_titles`) so these rare rules are
caught by hundreds of lines instead of three.

## Files
- `runs.tsv` — one row per port: wrong lines on old (of 2,000), wrong lines on new (of 100,000), caught-old,
  caught-new. Header row plus the oracle (`__oracle__`) and all 115 mutants.

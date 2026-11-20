# Day 5 hardening

## Holes closed

The original task at `a2bca77` gave one sixth of the reward for compilation alone. The hardened grader requires a successful build, a passing Python-cleanup and one-title smoke check, and at least 90% exact output matches before awarding overall credit. Once those conditions pass, it keeps the 4:1:1 weighting for behaviour, build, and cleanup. The individual scores still show how each submission performed.

| Control | Before reward | Before Harbor job | After reward | After Harbor job |
| --- | ---: | --- | ---: | --- |
| Echo input | 0.2307 | `mukul-before-control1` | 0.0 | `mukul-after-control1` |
| Build only | 0.1667 | `mukul-before-control2` | 0.0 | `mukul-after-control2` |
| Simple ASCII capitalization | 0.4530 | `mukul-before-control3` | 0.0 | `mukul-after-control3` |

The three after runs completed with zero exceptions. Echo accuracy fell from 9.60% to 1.37%, and simple capitalization fell from 42.95% to 15.99%. The small-word follow-up was described in Abhishek's report, and its script was unavailable in the report commit. The table covers the three published controls.

## Exam before and after

The old exam used 2,000 hidden titles. The new exam uses 100,000 unique titles generated with seed 1. The kit evaluated the original Python implementation twice in standard-library `re` mode at upstream revision `42f43e2de55bf003b286c6f8e8d8b2d26676a167`. Every pair was stable. The 100,000-title suite retains punctuation, Unicode, whitespace, and unchanged cases.

| Port | Wrong on old exam | Wrong on new exam | Chance a random 2,000 from the new pool misses all errors |
| --- | ---: | ---: | ---: |
| My original oracle | 0 of 2,000 | 857 of 100,000 | Rounds to 0% |
| Madhur Jain | 0 of 2,000 | 857 of 100,000 | Rounds to 0% |
| Ayush Singh | 0 of 2,000 | 0 of 100,000 | No errors observed |
| My corrected oracle | 0 of 2,000 | 0 of 100,000 | No errors observed |

The port comparison used Go 1.23.12 with CGO disabled and the kit's comparison script. The `measure/` files record the exact port sources and show the old and new results. These are direct binary measurements. The first hardened Harbor oracle run, `mukul-day5-hardened-oracle`, scored 0.9943 overall. The corrected oracle scored 1.0 with zero exceptions in `mukul-day5-hardened-oracle-v2`.

## What I learned

The larger exam exposed a rule the old exam missed. The Go implementation skipped an initial underscore as punctuation, so it changed `_dream` to `_Dream`. Python's `re` mode treats that underscore as a word character and leaves the word intact. I corrected the Go port and kept every exam case.

# Submission note

## Evaluation results

- Genuine Oracle: **1.000** (Behaviour 1.000, Build 1.000, No_Python 1.000)
- NOP: **0.000**
- Visible-answer cheat: **0.1667** (Behaviour 0.000, Build 1.000, No_Python 0.000)

Result screenshots are in `screenshots/oracle.png`, `screenshots/nop.png`, and `screenshots/cheat.png`.

## Common titlecase edge cases

The final Oracle result is fully passing and Harbor reports aggregate scores rather than per-rule miss counts. During port validation, the most repeated correction areas were small words at first/last positions after punctuation or slash recursion, preserving intentional mixed capitalization and acronyms, apostrophe prefixes such as `d'` and `o'`, and consonant-only words.

## Verifier hardening suggestion

Expand the verifier-only corpus with newly randomized hidden titles on each evaluation, and continue keeping those inputs and expected outputs inaccessible to the agent. This reduces the value of memorizing a fixed visible-answer table.

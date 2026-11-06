
## Harbor Evaluation Results

| Evaluation | Expected Score | Actual Score | Status |
|---|---:|---:|---|
| Oracle | 1.0 | 1.000 | PASS |
| Nop | 0.0 | 0.000 | PASS |
| Cheat | Below 0.2 | 0.167 | PASS |

## Reward Evidence

Screenshots of the three Harbor evaluation results:

- Oracle reward: 1.000
- Nop reward: 0.000
- Cheat reward: 0.167

## Task Reflection

1. **Rules the agent got wrong most often:** Sub-phrase capitalization after punctuation and Unicode dashes, apostrophe casing (such as `l'Grange` versus `O'Grange`), and preserving inline periods and mixed-case acronyms in all-caps lines. These cases were challenging when translating Python regex behavior into Go's standard library.

2. **What would make the task harder:** Extend the task to cover the optional callback handler and whitespace-related flags (`preserve_blank_lines` and `normalise_space_characters`), with additional hidden tests for multiline inputs, non-ASCII apostrophes, and Unicode punctuation.
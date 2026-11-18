# titlecase-go: Harbor Task (Siddharth Singh)

Port the Python `titlecase()` function of [python-titlecase](https://github.com/ppannuto/python-titlecase) (commit `42f43e2de55bf003b286c6f8e8d8b2d26676a167`) to Go with byte-identical output across thousands of varied titles.

## Evaluation Results

| Run | Reward | Build | No Python | Behaviour | Status |
|---|---|---|---|---|---|
| **Oracle** (`solution/solve.sh`) | **1.0000** | 1 | 1 | 1.0000 | ✅ Target 1.0 |
| **Cheat** (`cheat/solve.sh`) | **0.1670** | 1 | 0 | 0.0005 | ✅ Target < 0.2 |
| **Nop** (no solve script) | **0.0000** | 0 | 0 | 0.0000 | ✅ Target 0.0 |

Reward formula: `(build * 1 + no_python * 1 + behaviour * 4) / 6.0`

## Questions (Step 8 Hand-in)

1. **Which rules did the agent get wrong most?**
   - **Apostrophe prefixes with trailing quotes**: Words like `'o'reilly'` or `d'angelo'` ending with a bare quote `'` do not match Python's `APOS_SECOND` regex anchor `(?:['s]{2})?$` and must fall through to standard `capFirst`.
   - **Small words at line start/end**: Words like `AT&T` at line start matched the small-word boundary scanner for `at` → converting `AT&T` to `At&T`.
   - **Consonant-only acronyms with trailing punctuation**: In Python, `\A[consonants]+\Z` rejects words with trailing punctuation or quotes, falling through to `capFirst`.
   - **All-caps line preservation of honorifics**: `MR`, `MRS`, `MS`, `DR` remain fully uppercase in all-caps lines.

2. **What would you add to make the task harder?**
   - Non-ASCII Unicode punctuation variants (curly single/double quotes, en-dash, em-dash, non-breaking spaces).
   - Multi-line titlecasing preserving original paragraph indentation, trailing line breaks, and blank lines.
   - Callback support with immutable span tracking to match Python's full signature.

## Directory Structure

```
SiddharthSingh/
├── README.md
├── NOTES.md
└── titlecase-go/
    ├── instruction.md
    ├── task.toml
    ├── environment/
    │   ├── Dockerfile
    │   └── python-titlecase/
    ├── solution/
    │   └── solve.sh
    ├── cheat/
    │   └── solve.sh
    └── tests/
        ├── gen.py
        ├── test.sh
        ├── diff_check.sh
        └── data/
            ├── inputs.txt
            ├── expected.txt
            ├── hidden_inputs.txt
            └── hidden_expected.txt
```


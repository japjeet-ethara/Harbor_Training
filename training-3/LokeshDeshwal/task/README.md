# titlecase-go

This is a Harbor task where an AI agent ports the Python `titlecase` library to Go (standard library only).

| Run | Reward |
| --- | --- |
| oracle | 1.0000 |
| nop | 0.0000 |
| cheat | 0.1667 |

### Analysis

1. **Which rules the agent got wrong most:**
   - Case-insensitivity and punctuation handling on small words at the very end of lines (e.g. `smallLast` matching `v.` vs `V.`).
   - Package name collisions where naming the Go module `module titlecase` in `go.mod` blocked `go build ./...` because the existing `titlecase/` directory was left on disk.

2. **What would you add to make the task harder:**
   - Multi-language Unicode casing edge cases (e.g., German sharp-s `ß`, Turkish dotted/dotless `i`/`İ`, and curled apostrophes like `\u2019`).
   - Preserving complex inline HTML tags, custom domain extensions, and multi-paragraph input streams with varied indentation.

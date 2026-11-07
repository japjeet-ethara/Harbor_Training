# Harbor Task: titlecase-go

This task ports the MIT-licensed `python-titlecase` behavior to a standalone Go line filter. The agent reads one title per line from standard input and writes one title-cased result per line to standard output.

## Validation Evidence

| Check | Result |
|---|---:|
| Oracle | 1.0 |
| NOP | 0.0 |
| Cheat | 0.1667 |
| Hidden behavior | 1.0 |

The cheat result is below 0.2 because grading uses a separate hidden corpus that the cheat implementation does not access.

## 1. Rules the Agent Found Challenging

The main implementation challenge was translating Python regular-expression behaviour into Go. In particular, Go's `regexp` package does not support lookahead, lookbehind, or backreferences, so these behaviours had to be reproduced using manual character-by-character checks.

A frequency count of individual titlecase rule failures was not recorded.

## 2. Proposed Improvements to Increase Task Difficulty

The task could be made more challenging by expanding the hidden test dataset with additional edge cases and combinations involving small words at the beginning and end of titles, apostrophes, hyphenated words, acronyms, URLs, ordinal numbers, punctuation, Unicode characters, and whitespace.

All outputs should continue to be evaluated using exact byte-for-byte matching against the reference implementation.

## Author

**VANAM PRASHANTH**

GitHub: [@prashanthvanamethara](https://github.com/prashanthvanamethara)
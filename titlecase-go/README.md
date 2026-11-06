## 1. Rules the Agent Found Challenging

The main implementation challenge was translating Python
regular-expression behaviour into Go. In particular, Go's `regexp`
package does not support lookahead, lookbehind, or backreferences, so
these behaviours had to be reproduced using manual
character-by-character checks. A frequency count of individual titlecase
rule failures was not recorded.

## 2. Proposed Improvements to Increase Task Difficulty

The task could be made more challenging by expanding the hidden test
dataset with additional edge cases and combinations involving small
words at the beginning and end of titles, apostrophes, hyphenated words,
acronyms, URLs, ordinal numbers, punctuation, Unicode characters, and
whitespace. All outputs should continue to be evaluated using exact
byte-for-byte matching against the reference implementation.

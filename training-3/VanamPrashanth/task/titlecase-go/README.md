# Harbor Task: titlecase-go

This task ports the MIT-licensed `python-titlecase` behavior to a standalone Go line filter. The agent reads one title per line from standard input and writes one title-cased result per line to standard output.

## Validation Evidence

| Check | Result | Criteria Breakdown |
|---|---:|---|
| **Oracle** | **1.000** | `build`: 1.0, `no_python`: 1.0, `behaviour`: 1.0 (2,000/2,000 hidden cases) |
| **NOP** | **0.000** | `build`: 0.0, `no_python`: 0.0, `behaviour`: 0.0 |
| **Cheat** | **0.1667** | `build`: 1.0, `no_python`: 0.0, `behaviour`: 0.0 (< 0.20 threshold) |

The cheat result is strictly 0.1667 (< 0.20) because grading uses a separate hidden corpus (2,000 cases) that the cheat implementation does not access, and `cheat/solve.sh` does not remove `.py` files.

### Oracle Evaluation
![Oracle Evaluation Output](reward%20images/oracle.png)

### NOP Evaluation
![NOP Evaluation Output](reward%20images/nop.png)

### Cheat Evaluation
![Cheat Evaluation Output](reward%20images/cheat.png)

## 1. Rules the Agent Found Challenging (Rules the Agent Got Wrong Most)

The primary technical hurdle was that Go's standard `regexp` engine does not support lookahead, lookbehind, or backreferences (unlike Python's `re`). The specific rules the agent failed most often:

1. **Rule 4 (Sub-Phrase Breaks)**: Small words immediately following punctuation breaks (`:`, `;`, `.`, `?`, `!`, `-`, `–`, `—`) followed by space must be capitalized (e.g. `'Title: a Test'` $\to$ `'Title: A Test'`). The agent frequently treated these as ordinary mid-title small words and kept them lowercase.
2. **Rule 7 (Mixed-Case / Internal Uppercase Words)**: Words with existing uppercase letters later in the word (e.g. `iTunes`, `AT&T`, `Q&A`) must be preserved verbatim. The agent repeatedly flattened them or blindly title-cased them.
3. **Rule 9 & 10 (Apostrophe & Prefix Rules)**: Words starting with `d'`, `o'`, `l'` or `Mc` have asymmetric casing rules (e.g., `o'grange` $\to$ `O'Grange` with vowel capitalized, `l'grange` $\to$ `l'Grange` with lowercase leading consonant, and `mccarthy` $\to$ `McCarthy`). Agents struggled to implement these without regex lookarounds.
4. **Rule 14 (All-Consonant Acronyms)**: Words of more than two letters composed entirely of consonants must be uppercased as acronyms (e.g. `cnn` $\to$ `CNN`, but `st` stays lowercase/title-cased). The agent failed to identify vowel presence (`y` counting as a vowel) and length thresholds.
5. **Rule 12 & 13 (Slash & Hyphen Compounding)**: Compound words (`and/or`, `end-to-end`) require splitting each segment while disabling the first/last word capitalization rule for internal components.

## 2. Proposed Improvements to Increase Task Difficulty

To make the task even harder for frontier models:
1. **Expand the Hidden Dataset with Complex Unicode Combinations**: Introduce non-ASCII Unicode apostrophes (curly single quote `‘`, right single quote `’`), em-dashes (`—`), en-dashes (`–`), and horizontal bars (`―`), combined with multi-byte accents (e.g., German umlauts, French accents, Scandinavian ligatures).
2. **Interleaved URL & Protocol Edge Cases**: Include obscure protocol handlers (`sftp://`, `magnet:?`, `file:///`) and domain names ending in unusual TLDs (`.co.uk`, `.photography`), forcing the model to distinguish between URL boundaries and natural language words.
3. **Strict Memory and Zero-Allocation Constraints**: Require the Go port to operate within strict memory caps (e.g., `< 16MB` memory footprint) or evaluate execution latency on million-line stream inputs to test algorithmic efficiency.

## Author

**VANAM PRASHANTH**  
Email: `vanam.prashanth@ethara.ai`  
GitHub: [@prashanthvanamethara](https://github.com/prashanthvanamethara)

Titlecase Go Harbor Task

### 1. Evaluation Results

| Evaluation | Reward |
|---|---:|
| Oracle | 1.0 |
| Nop | 0.0 |
| Cheat | 0.167 |

### 2. Rules Failed Most Often

Sub-phrase capitalization following Unicode dashes and punctuation (`:`, `—`, `–`, `‒`, `―`), consonant/vowel apostrophe casing (`l'Grange` vs `O'Grange`), and preserving inline periods and mixed-case acronyms on all-caps lines.

### 3. Hardening Suggestions

Require implementing the optional callback handler and whitespace/blank-line flags (`preserve_blank_lines` and `normalise_space_characters`) across multi-line inputs with non-ASCII Unicode apostrophes and punctuation.

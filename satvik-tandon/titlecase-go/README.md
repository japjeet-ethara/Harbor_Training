# Harbor task: titlecase-go

This task ports the MIT-licensed `python-titlecase` behavior to a standalone
Go line filter. The agent reads one title per line from stdin and writes one
title-cased result per line to stdout.

## Validation evidence

| Check | Result |
|---|---:|
| Oracle | 1.0 |
| Nop | 0.0 |
| Cheat | 0.1667 |
| Hidden behavior | 1.0 |

The cheat result is below 0.2 because grading uses a separate hidden corpus.

## Assessment notes

The most error-prone rules were apostrophe forms such as `d'Artagnan`,
punctuation-delimited small words, and mixed/all-capital tokens. A fair
hardening improvement would add a larger independently generated corpus with
Unicode letters, repeated whitespace, and additional punctuation edge cases.

## Run locally

```text
harbor run --path . --agent oracle
harbor run --path . --agent nop
```

The source snapshot and deterministic visible/hidden datasets are included in
the task package for reproducible assessment.

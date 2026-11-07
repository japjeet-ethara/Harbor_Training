# Madhur Jain — titlecase-go Harbor task

Port of python-titlecase to Go, graded byte for byte on 2,000 hidden titles.

| Run | Reward | Screenshot |
| --- | --- | --- |
| Oracle | 1.0 | titlecase-go/screenshots/oracle.png |
| Nop | 0.0 | titlecase-go/screenshots/nop.png |
| Cheat | 0.167 (behaviour 0.0) | titlecase-go/screenshots/cheat.png |


**Rules the agent got wrong most:** Unicode words (rules 11 and 17), because Python's `\w` matches any letter, such as `é` or `ß`, while Go's `\w` is ASCII only; all-caps lines (rules 6 and 15), where initials like `U.S.` must stay and every other word is lowered first; and small words at the start or end of a line next to punctuation (rules 18 and 19).

**To make the task harder I would add:** more hidden titles that combine several rules at once (an all-caps line with a hyphenated word, a slash and a small word at the end) and more non-English words (`ß`, accented capitals); and I would block the agent's internet so it cannot download an existing Go titlecase port.

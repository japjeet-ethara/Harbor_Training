# Attack Report

Target: Uday Bhatnagar
Target commit: `5139952601ef72fccac3c378e24ac0e60402e9d7`
Target task: `Uday-Bhatnagar/titlecase-go`

The task rewards build, no-Python and behavior with the formula:
`(build × 1 + no_python × 1 + behavior × 4) / 6`.

## Cheat 1 - Direct hidden-answer read

What it does:
The submitted Go binary reads `hidden_expected.txt` from the verifier mount and
writes it directly to standard output.

Score: `1.0000`

- build: `1.0`
- no_python: `1.0`
- behavior: `1.0`

Job folder: `Harbor_Training/TannuKumari/jobs/uday-cheat4-hidden-read`
Trial: `uday-cheat4__9NQTPqh`

Why it worked:
The submitted binary could open `/tests/data/hidden_expected.txt` during
verifier execution. This bypassed the titlecase implementation completely.

How to fix:
Do not mount hidden answers anywhere accessible to the submitted process.
The verifier must compare outputs outside the submitted program's filesystem
namespace.

## Cheat 2 - Hidden-answer read with Python retained

What it does:
It performs the same direct hidden-answer read but leaves the original Python
implementation in the workspace.

Score: `0.8333`

- build: `1.0`
- no_python: `0.0`
- behavior: `1.0`

Job folder:
`Harbor_Training/TannuKumari/jobs/uday-cheat5-hidden-read-py-remains`
Trial: `uday-cheat5__CQEBgLC`

Why it worked:
The answer read supplied every hidden expected line, so behavior received
full credit. Only the independent no-Python check lost a point.

How to fix:
Protect hidden answers and combine no-Python checking with behavior verification.
Python source left behind should not merely lose one independent point.

## Cheat 3 - Lookup table

What it does:
The Go program embeds Uday's visible input/expected-answer pairs. It returns
the visible answer for a match and echoes unseen input for anything else.

Score: `0.3333`

- build: `1.0`
- no_python: `1.0`
- behavior: `0.0`

Job folder: `Harbor_Training/TannuKumari/jobs/uday-cheat1-r3`
Trial: `uday-cheat1__2Kq8yD5`

Why it worked:
It passed build and no-Python because both are independent of real titlecasing
behavior. Hidden behavior was zero because Uday's visible and hidden datasets
do not overlap.

How to fix:
Keep visible answers inaccessible and tie build/no-Python points to meaningful
behavior. Hidden inputs should test correct implementation beyond copied tables.

The highest score was `1.0000` from direct hidden-answer reading.

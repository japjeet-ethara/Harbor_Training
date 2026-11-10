# Regression Cases for the Three Bug Fixes

These cases are NOT part of the official test data (`tests/data/`).
They document the exact inputs and expected outputs that each bug fix addresses.
Run them manually against the binary after `solve.sh` completes.

---

## Bug 1 — `capFirst` must not capitalize the letter after a digit

| Input | Expected | Previously actual |
|---|---|---|
| `FOO BAR 5TH ST` | `Foo Bar 5th St` | `Foo Bar 5Th St` |
| `1ST PLACE` | `1st Place` | `1St Place` |
| `2ND FLOOR` | `2nd Floor` | `2Nd Floor` |
| `3RD STREET` | `3rd Street` | `3Rd Street` |
| `21ST CENTURY` | `21st Century` | `21St Century` |
| `34TH AVENUE` | `34th Avenue` | `34Th Avenue` |

Root: `capFirst` previously skipped all non-letter chars (including digits) and uppercased
the first letter it found. Python's `CAPFIRST = r"^[PUNCT]*?([\p{Letter}])"` regex anchors at
start, allows only PUNCT before the letter, so a digit at position 0 makes the regex fail
entirely — the word is returned unchanged.

---

## Bug 2 — `applySmallLast` must cross hyphens and slashes to find the last small word

| Input | Expected | Previously actual |
|---|---|---|
| `open valley thunder-v.-Paper-a` | `Open Valley Thunder-v.-Paper-A` | `Open Valley Thunder-v.-Paper-a` |
| `Light circle east-or-journal-by` | `Light Circle East-or-Journal-By` | `Light Circle East-or-Journal-by` |
| `captain EAST zebra final-and-west-of` | `Captain EAST Zebra Final-and-West-Of` | `Captain EAST Zebra Final-and-West-of` |
| `DANCE engine RIVER-to-garden-at` | `DANCE Engine RIVER-to-garden-At` | `DANCE Engine RIVER-to-garden-at` |
| `Forest APPLE-en-south-an` | `Forest APPLE-en-south-An` | `Forest APPLE-en-south-an` |
| `Music THUNDER Silver Harbor-in-West-v` | `Music THUNDER Silver Harbor-in-West-V` | `Music THUNDER Silver Harbor-in-West-v` |

Root: `applySmallLast` previously scanned back only to the last **space**, making the entire
hyphenated token the candidate (e.g. `"thunder-v.-paper-a"`), which is never a small word.
Python's `SMALL_LAST = r'\b(small_word)[PUNCT]?$'` uses `\b` which fires at any word boundary
including between `-` and a letter. Fix: scan back to the last run of letters only.

---

## Bug 3 — `hasUCElsewhere` must not cross hyphens

| Input | Expected | Previously actual |
|---|---|---|
| `Dr Mcmaier-Mcfoo bridge garden` | `Dr McMaier-McFoo Bridge Garden` | `Dr Mcmaier-Mcfoo Bridge Garden` |
| `mrs Mccay-Mcintosh market SUMMER` | `Mrs McCay-McIntosh Market SUMMER` | `Mrs Mccay-Mcintosh Market SUMMER` |
| `MR MCdavid-mcdonald Story BROKEN NORTH` | `MR McDavid-McDonald Story BROKEN NORTH` | `MR Mcdavid-mcdonald Story BROKEN NORTH` |

Root: After `matchMacMc` splits `"Mcmaier-Mcfoo"` into prefix `"Mc"` and rest `"maier-Mcfoo"`,
the recursive call processes `"maier-Mcfoo"`. The old `hasUCElsewhere` scanned through `-`
(a non-letter, non-PUNCT char that it previously ignored), finding `'m'` then `'M'` and
returning `true` — which left the word unchanged. Python's `UC_ELSEWHERE.match()` stops at
`-` because `[\p{Letter}]+` cannot match it, so the match fails. Fix: reset `seenLetter=false`
when a non-letter character is encountered.

---

## How to run manually (after solve.sh completes)

```bash
echo "FOO BAR 5TH ST"             | /tmp/titlecase  # expect: Foo Bar 5th St
echo "open valley thunder-v.-Paper-a" | /tmp/titlecase  # expect: Open Valley Thunder-v.-Paper-A
echo "Dr Mcmaier-Mcfoo bridge garden" | /tmp/titlecase  # expect: Dr McMaier-McFoo Bridge Garden
```

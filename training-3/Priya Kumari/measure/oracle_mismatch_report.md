# Oracle Mismatch Diagnostic Report (Day 5 Measurement)

## 1. Summary Metrics
- **Total Exam Titles:** 100,000
- **Correct Outputs:** 99,143 (99.143%)
- **Total Mismatches Verified:** 857 (0.857%)
- **Verification Status:** Read-only inspection against `key/answers.txt`.

---

## 2. Root Cause Analysis
Every single mismatch (857 out of 857, **100.0%**) is caused by a single architectural divergence:
**Treatment of Underscore (`_`) in Word Boundaries and `CAPFIRST` Regex.**

### Mechanics of the Discrepancy:
1. **Python `re` (Standard Library, No `regex` package):**
   - `PUNCT` includes `_` (`_` is in `punctSet`).
   - `CAPFIRST = re.compile(r"^[%s]*?([\w])" % PUNCT)`
   - In Python's built-in `re`, `\w` **includes underscore `_`** (`[a-zA-Z0-9_]`).
   - Because `*?` is non-greedy, on an input starting with `_` (e.g. `_winter` or `_via`):
     - `^[%s]*?` matches 0 characters (empty match).
     - `([\w])` immediately matches the initial `_`.
     - `CAPFIRST.sub(...)` upper-cases `_` $\rightarrow$ `_`, leaving the rest of the word in lowercase (`_winter`, `_via`).
2. **Go Oracle (`main.go`):**
   - `capFirst(word)` treats `_` purely as punctuation (`isPunct(rs[i])`).
   - It advances past `_`, finds the first alphanumeric letter, and capitalizes it (`_Winter`, `_Via`).
   - Similarly, compound/slash handling and small-word checks in Go treat `_` as a boundary, whereas Python's `re` regexes fail to match small words or consonant acronyms when prefixed with `_`.

---

## 3. Error Categories & Overlap Breakdown

> [!NOTE]
> **Category Overlap Explanation:**
> Categories naturally overlap because a single title or token can carry multiple characteristics (e.g., an underscore-prefixed token can be both a hyphenated compound and contain punctuation like `_out-of-Date#`, or a small word with Unicode whitespace).

| Category | Count | % of Mismatches | Description |
| :--- | :---: | :---: | :--- |
| **Underscore + Normal Word** | 487 | 56.8% | Regular vocabulary words prefixed with `_` (e.g. `_winter`, `_dream`). Go capitalized the first letter; Python left it lowercase. |
| **Underscore + Small Word** | 240 | 28.0% | New York Times small words prefixed with `_` (e.g. `_via`, `_the`, `_v`). Python did not recognize them as isolated small words; Go stripped `_` and capped them. |
| **Underscore + Hyphenated / Slash Compound** | 96 | 11.2% | Hyphenated or slash compounds prefixed with `_` (e.g. `_and/or`, `_out-of-Date`). Go parsed internal words; Python left the head lowercase. |
| **Underscore + All-Consonant Acronym** | 37 | 4.3% | Consonant acronyms prefixed with `_` (e.g. `_pdf;`, `_nth`). Python consonant regex failed due to `_`; Go stripped `_` and treated as acronym. |
| **Underscore + Additional Punctuation** | 243 | 28.4% | Underscore-prefixed tokens that also carry trailing/enclosing punctuation marks (e.g. `_dream#`, `_pdf;`). |
| **Underscore + Unicode Character** | 40 | 4.7% | Titles where the underscore token appears adjacent to non-ASCII runes or Unicode spaces. |

---

## 4. Representative Examples by Category

### Category: Underscore + Normal Word (487 occurrences)
| Line # | Input Title | Expected (`key/answers.txt`) | Got (`ports/my-oracle/got.txt`) | Mismatched Token (Want vs Got) |
| :---: | :--- | :--- | :--- | :--- |
| `396` | `-lead _winter https://x.org ıstanbul xkcd` | `-Lead _winter https://x.org Istanbul XKCD` | `-Lead _Winter https://x.org Istanbul XKCD` | `_winter` vs `_Winter` |
| `568` | `macintosh a/b/c _dream input/output` | `Macintosh a/B/C _dream Input/Output` | `Macintosh a/B/C _Dream Input/Output` | `_dream` vs `_Dream` |
| `640` | `on to WINTER _ocean -lead iPhone% garden MS? at` | `On to WINTER _ocean -Lead iPhone% Garden MS? At` | `On to WINTER _Ocean -Lead iPhone% Garden MS? At` | `_ocean` vs `_Ocean` |
| `935` | `A.B. winter _dream ftp://host/file BBC. via` | `A.B. Winter _dream Ftp://host/file BBC. Via` | `A.B. Winter _Dream Ftp://host/file BBC. Via` | `_dream` vs `_Dream` |

### Category: Underscore + Small Word (240 occurrences)
| Line # | Input Title | Expected (`key/answers.txt`) | Got (`ports/my-oracle/got.txt`) | Mismatched Token (Want vs Got) |
| :---: | :--- | :--- | :--- | :--- |
| `328` | `JavaScript to ıstanbul for( _via vs night the` | `JavaScript to Istanbul For( _via vs Night The` | `JavaScript to Istanbul For( _Via vs Night The` | `_via` vs `_Via` |
| `337` | `of дом and MRS _via` | `Of Дом and MRS _via` | `Of Дом and MRS _Via` | `_via` vs `_Via` |
| `976` | `Rhythm summer via gTLD crwth% via _en music as{` | `Rhythm Summer via gTLD Crwth% via _en Music As{` | `Rhythm Summer via gTLD Crwth% via _En Music As{` | `_en` vs `_En` |
| `1671` | `αlpha“ the  i.e. iPhone house _v` | `Αlpha“ the  i.e. iPhone House _v` | `Αlpha“ the  i.e. iPhone House _V` | `_v` vs `_V` |

### Category: Underscore + Hyphenated / Slash Compound (96 occurrences)
| Line # | Input Title | Expected (`key/answers.txt`) | Got (`ports/my-oracle/got.txt`) | Mismatched Token (Want vs Got) |
| :---: | :--- | :--- | :--- | :--- |
| `264` | `-lead _and/or MCDONALD by #life an} data` | `-Lead _and/or McDonald by #Life An} Data` | `-Lead _And/or McDonald by #Life An} Data` | `_and/or` vs `_And/or` |
| `880` | `for story o'neil garden mrs. summer _out-of-date v` | `For Story O'Neil Garden Mrs. Summer _out-of-Date V` | `For Story O'Neil Garden Mrs. Summer _Out-of-Date V` | `_out-of-Date` vs `_Out-of-Date` |
| `1270` | `_out-of-date “if winter v. e.g. node.js -lead for i.e.` | `_out-of-Date “If Winter v. e.g. node.js -Lead for i.e.` | `_Out-of-Date “If Winter v. e.g. node.js -Lead for i.e.` | `_out-of-Date` vs `_Out-of-Date` |
| `2208` | `guide MCDONALD mcdonald _self-made` | `Guide McDonald McDonald _self-Made` | `Guide McDonald McDonald _Self-Made` | `_self-Made` vs `_Self-Made` |

### Category: Underscore + All-Consonant Acronym (37 occurrences)
| Line # | Input Title | Expected (`key/answers.txt`) | Got (`ports/my-oracle/got.txt`) | Mismatched Token (Want vs Got) |
| :---: | :--- | :--- | :--- | :--- |
| `839` | `A.B.C _pdf; MS garden` | `A.B.C _pdf; MS Garden` | `A.B.C _Pdf; MS Garden` | `_pdf;` vs `_Pdf;` |
| `1438` | `on heart; for re-enter winter _nth` | `On Heart; For Re-Enter Winter _nth` | `On Heart; For Re-Enter Winter _Nth` | `_nth` vs `_Nth` |
| `2043` | `heart _A.B.C _nth guide PDF; l‘oiseau NODE.JS! life. vs` | `Heart _A.B.C _nth Guide PDF; l‘Oiseau NODE.JS! Life. Vs` | `Heart _A.B.C _Nth Guide PDF; l‘Oiseau NODE.JS! Life. Vs` | `_nth` vs `_Nth` |
| `2582` | `THE- GUIDE BBC*	_nth` | `The- GUIDE BBC*	_nth` | `The- GUIDE BBC*	_Nth` | `_nth` vs `_Nth` |

### Category: Underscore + Additional Punctuation (243 occurrences)
| Line # | Input Title | Expected (`key/answers.txt`) | Got (`ports/my-oracle/got.txt`) | Mismatched Token (Want vs Got) |
| :---: | :--- | :--- | :--- | :--- |
| `264` | `-lead _and/or MCDONALD by #life an} data` | `-Lead _and/or McDonald by #Life An} Data` | `-Lead _And/or McDonald by #Life An} Data` | `_and/or` vs `_And/or` |
| `839` | `A.B.C _pdf; MS garden` | `A.B.C _pdf; MS Garden` | `A.B.C _Pdf; MS Garden` | `_pdf;` vs `_Pdf;` |
| `880` | `for story o'neil garden mrs. summer _out-of-date v` | `For Story O'Neil Garden Mrs. Summer _out-of-Date V` | `For Story O'Neil Garden Mrs. Summer _Out-of-Date V` | `_out-of-Date` vs `_Out-of-Date` |
| `1270` | `_out-of-date “if winter v. e.g. node.js -lead for i.e.` | `_out-of-Date “If Winter v. e.g. node.js -Lead for i.e.` | `_Out-of-Date “If Winter v. e.g. node.js -Lead for i.e.` | `_out-of-Date` vs `_Out-of-Date` |

### Category: Underscore + Unicode Character (40 occurrences)
| Line # | Input Title | Expected (`key/answers.txt`) | Got (`ports/my-oracle/got.txt`) | Mismatched Token (Want vs Got) |
| :---: | :--- | :--- | :--- | :--- |
| `3619` | `if _xkcd“ heart for J.R.R. of \|as` | `If _xkcd“ Heart for J.R.R. Of \|As` | `If _Xkcd“ Heart for J.R.R. Of \|As` | `_xkcd“` vs `_Xkcd“` |
| `3781` | `_l‘oiseau light` | `_l‘oiseau Light` | `_L‘oiseau Light` | `_l‘oiseau` vs `_L‘oiseau` |
| `7423` | `en island mcgraw-hill iPhone _l‘oiseau but` | `En Island McGraw-Hill iPhone _l‘oiseau But` | `En Island McGraw-Hill iPhone _L‘oiseau But` | `_l‘oiseau` vs `_L‘oiseau` |
| `7883` | `winter. _straße world` | `Winter. _straße World` | `Winter. _Straße World` | `_straße` vs `_Straße` |

---

## 5. Suggested Fix Priorities

If hardening the Go Oracle in a future iteration to achieve 100.00% matching against Python's `re` fallback mode:

1. **Priority 1: Replicate Python `\w` including `_` in `capFirst()`**
   - In `ports/my-oracle/main.go`, `capFirst(word)` loops while `isPunct(r)`. Because `punctSet` contains `_`, `capFirst` skips `_`.
   - In Python `re`, `\w` matches `_`. Since `^[%s]*?([\w])` is non-greedy, it matches `_` as the first word character and capitalizes `_` to `_`, leaving letters after `_` un-capitalized.
   - **Fix:** If a word begins with `_`, treat `_` as the first character (do not skip past it to capitalize subsequent letters).
   - **Impact:** Eliminates ~700+ of the 857 mismatches immediately.

2. **Priority 2: Replicate Python `\A...\Z` Anchoring on Compounds and Small Words**
   - In Python, `SMALL_WORDS = re.compile(r'^(%s)$' % SMALL)` has strict string boundaries. A token like `_via` or `_the` does not match `SMALL_WORDS` because of the leading `_`.
   - In Go, `applySmallFirst()` strips `_` before matching small words.
   - **Fix:** Ensure small-word and acronym lookup only strips standard quotation/bracket punctuation, not leading `_`.
   - **Impact:** Eliminates the remaining ~150 mismatches on small words and slash/hyphen compounds.

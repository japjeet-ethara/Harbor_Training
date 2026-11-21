# Source notes

Repo: https://github.com/ppannuto/python-titlecase
Commit: 42f43e2de55bf003b286c6f8e8d8b2d26676a167
Date:   2024-04-05T22:03:59-07:00
Licence: MIT
Reference engine: regex (verified, not the re fallback)

Verified examples:
  the lord of the rings   -> The Lord of the Rings
  mac mc MAC MC machine   -> Mac Mc MAC MC Machine

Rules from titlecase/__init__.py:
1. SMALL words lowercased mid-title: a an and as at but by en for if in of on or the to v(.) via vs(.)
2. First and last word capitalised even when SMALL (SMALL_FIRST / SMALL_LAST).
3. UC_INITIALS preserved verbatim, only when the entire line is upper case.
4. APOS_SECOND: d/l/o + apostrophe. o'reilly -> O'Reilly, l'grange -> l'Grange.
5. MAC_MC is CASE-SENSITIVE: ^([Mm]c|MC)(\w.+)  matches Mc/mc/MC, NOT mac/MAC.
   This is why "mac mc MAC MC machine" -> "Mac Mc MAC MC Machine".
6. MR_MRS_MS_DR (case-insensitive, full match): uppercase first letter only, rest untouched.
7. Inline letter.letter, or an internal capital when line is not all-caps -> word untouched.
8. "/" split (unless "//") and "-" split; each part titlecased with small_first_last=False.
9. All-ASCII-consonant words longer than 2 chars -> UPPER (cnn -> CNN, mss -> MSS).
10. SUBPHRASE is CASE-SENSITIVE: after ": . ; ? ! - en-dash em-dash" + space,
    a lowercase SMALL word is capitalised.
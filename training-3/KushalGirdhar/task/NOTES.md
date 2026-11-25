# Reference notes

The upstream source is python-titlecase 2.4.1 at [commit 42f43e2de55bf003b286c6f8e8d8b2d26676a167](https://github.com/ppannuto/python-titlecase/commit/42f43e2de55bf003b286c6f8e8d8b2d26676a167).
Git reports the commit date as `2024-04-05T22:03:59-07:00`. The upstream [MIT license](environment/repo/LICENSE.txt) credits Patrick William Pannuto. See its [contributors list](environment/repo/AUTHORS.rst).

These examples were run through the unmodified function with default options in CPython 3.12.14, Unicode 15.0.0, and standard-library `re`. Python repr escapes make separator bytes and Unicode code points visible.

| # | Rule | Input | Output |
| --- | --- | --- | --- |
| 1 | Line boundaries and whitespace | `' the  daemon\tand\xa0the cache '` | `' the  Daemon\tand\xa0the Cache '` |
| 2 | All-caps initials | `'A.B. AND THE DISPATCH'` | `'A.B. And the Dispatch'` |
| 3 | Apostrophe names | `"d'angelo and o'neill"` | `"d'Angelo and O'Neill"` |
| 4 | Mc recursion with edge capitalization | `'mcand and mcdonald'` | `'McAnd and McDonald'` |
| 5 | Honorific first character | `'dR and mRs on call'` | `'DR and MRs on Call'` |
| 6 | Inline period protection | `'sdk.api and 3.12 release'` | `'sdk.api and 3.12 Release'` |
| 7 | Internal ASCII uppercase protection | `'the openAPI and _iSCSI path'` | `'The openAPI and _iSCSI Path'` |
| 8 | Whole-token small words | `'install via the release gate'` | `'Install via the Release Gate'` |
| 9 | Slash recursion and double-slash protection | `'read/in/write and read//write'` | `'Read/in/Write and Read//write'` |
| 10 | Hyphen recursion | `'end-to-end and read-only/in-band notes'` | `'End-to-End and Read-Only/in-Band Notes'` |
| 11 | Consonant acronyms and minimum length | `'dns and bgp on rt'` | `'DNS and BGP on Rt'` |
| 12 | All-caps normalization | `'CACHE FOR THE WORKER'` | `'Cache for the Worker'` |
| 13 | First word character and Unicode expansions | `'\u201c\xdfeta and \ufb03le uploads'` | `'\u201cSSeta and FFIle Uploads'` |
| 14 | First and last small-word passes | `'[the alert goes on]'` | `'[The Alert Goes On]'` |
| 15 | Subphrase capitalization after exactly one space | `'ready: the relay?  in the loop'` | `'Ready: The Relay?  in the Loop'` |
| 16 | Contextual Greek final sigma | `'\u039f\u03a3 AND \u0391\u03a3\u02b0'` | `'\u039f\u03c2 and \u0391\u03c2\u02b0'` |

In the first pass, initials are conditional on all-caps detection. Apostrophe names, Mc names, honorifics, and inline-dot or mixed-case protection precede small words and compounds. All-caps lowering, consonant acronyms, and ordinary capitalization are the fallbacks. The edge and subphrase passes occur after token-level conversion.

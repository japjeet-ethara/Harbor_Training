# Context of the submission approaches

The comparison considered all 54 retrieved primary solutions, with 52 compiled programs evaluated. The categories below overlap: they describe implementation choices, not an official ranking or exhaustive review of each candidate's full task infrastructure. See COMPARISON.md for every participant and the audit limits.

| Approach | What it does | Strength and limitation |
|---|---|---|
| Compact heuristic ports | Implement a small-word list, capitalization, and a few name/compound rules | Easy to follow; simplified separators, punctuation, and rule order can change behavior |
| Regex-assisted ports | Translate supported patterns to Go regexp and handle unsupported features separately | Keeps pattern structure visible; Go and Python word classes, boundaries, and case folding differ |
| Manual rune matchers | Recreate patterns and boundary checks with explicit character processing | Gives control over alternation and match order; character properties still need careful compatibility |
| Unicode compatibility ports | Add Python casing expansions and character-property tables to either engine | Handles cases ordinary Go casing misses; reference/runtime versions must be explicit |
| Frozen-output replay | Embed visible answers and print them regardless of input | A useful negative control; it does not implement the function |

## The four requested submissions

- **Gunjit:** a manual rune-matcher port with ordered small-word alternatives, explicit boundaries, and a selected casing-expansion map. It addresses several subtle Python/Go differences. The selected map and approximate word class leave broader compatibility questions. Audit agreement: 95.238%.
- **Paniv_Kapoor:** a manual character-processing port with an explicit whitespace set, recursive compound handling, and Python-oriented casing helpers. It reads records with ReadString. Audit agreement: 94.548%.
- **VanamPrashanth-titlecase-go:** a mixed regexp and manual-rule port. It preserves individual separators, but defines word characters using letters, digits, and underscore and uses Go's native casing. Its Scanner-based input path is another contract consideration. Audit agreement: 85.497%.
- **satvik-tandon:** a compact port mixing regexp and manual rules. It splits titles on literal spaces and uses Go's native casing. This makes the implementation short, while leaving whitespace and Unicode behavior less complete. Audit agreement: 28.457%.

The repository spells these names Paniv_Kapoor and satvik-tandon; those are the entries used for the requested Praniv/Satvik review.

## How the new versions fit

Kushal uses explicit rune matchers and a balanced rule matrix. Hardika uses supported compiled patterns, with explicit handling where Go regexp cannot express Python behavior, and an interaction-based corpus. Both use generated compatibility tables derived from the pinned Python runtime rather than a short handwritten exception list. Their engines and datasets differ; the grading infrastructure is shared.

Both matched all 100,000 audit records. KumailMujtaba also matched all records using a manual matcher and compatibility tables. The evidence therefore supports a tie for the best observed functional result. Scores for other candidates can reflect different reference modes or input contracts, so they must not be treated as official grades.

## Komal addition

Komal's third version uses an explicit stack to schedule document, line, token, and assembly operations. It shares Unicode compatibility primitives and the grader, but has a different evaluation engine and a balanced editorial corpus: 16 families, 125 records per family in each split. All 4,000 inputs are distinct from both earlier corpora. It matched the same 100,000-record audit; the candidate comparison was not rerun.

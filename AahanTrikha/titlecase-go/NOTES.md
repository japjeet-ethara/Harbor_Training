# python-titlecase Analysis

## Repository Information
- **URL**: https://github.com/ppannuto/python-titlecase
- **Git SHA**: (To be filled in by user - run: `git log -1 --format='%H %cI'`)
- **License**: MIT License
- **Version**: 2.4.1

## License
**MIT License** - Copyright (c) 2021 Patrick William Pannuto

## Titlecase Rules

The `titlecase()` function applies the following rules in order:

### 1. **Small Words Rule**
Small words (a, an, and, as, at, but, by, en, for, if, in, of, on, or, the, to, v, v., via, vs, vs.) are lowercased unless they're the first or last word.

**Example Input**: `"the lord of the rings"`  
**Expected Output**: `"The Lord of the Rings"`

### 2. **First and Last Word Capitalization**
The first and last words are always capitalized, even if they are small words (when `small_first_last=True`, which is the default).

**Example Input**: `"a tale of two cities"`  
**Expected Output**: `"A Tale of Two Cities"`

### 3. **ALL CAPS + Initials Preservation**
If input is all uppercase and contains initials (like "U.S.A." or "A.B."), preserve them as-is.

**Example Input**: `"NASA AND THE FBI"`  
**Expected Output**: `"NASA AND THE FBI"` (if detected as initials)

### 4. **Apostrophe Second Character (O'Neill, D'Angelo pattern)**
Words starting with d/o/l followed by an apostrophe (e.g., O'Neill, d'Angelo, l'esprit) get special treatment: first letter case depends on vowel, third letter is capitalized.

**Example Input**: `"o'neill and d'angelo"`  
**Expected Output**: `"O'Neill and D'Angelo"`

### 5. **Mc/Mac Names**
Words starting with "Mc" or "Mac" followed by more characters are treated as surnames and recursively titlecased after the prefix.

**Example Input**: `"mcdonald and mcarthur"`  
**Expected Output**: `"McDonald and McArthur"`

### 6. **Titles: Mr, Mrs, Ms, Dr**
These honorifics are capitalized with first letter uppercase.

**Example Input**: `"mr smith and dr jones"`  
**Expected Output**: `"Mr Smith and Dr Jones"`

### 7. **Inline Periods (abbreviations like i.e., e.g.)**
Words containing periods with letters on both sides are preserved as-is.

**Example Input**: `"e.g. this and i.e. that"`  
**Expected Output**: `"e.g. This and i.e. That"` (inline periods preserved)

### 8. **Mixed Case Preservation (UC_ELSEWHERE)**
If a word has uppercase letters elsewhere (not just first letter) and input is not all caps, preserve it (e.g., iPhone, eBay).

**Example Input**: `"iPhone meets macOS"`  
**Expected Output**: `"iPhone Meets macOS"`

### 9. **Slash-Separated Words**
Words with "/" (but not "//") are split, each part titlecased recursively, then rejoined.

**Example Input**: `"read/write and input/output"`  
**Expected Output**: `"Read/Write and Input/Output"`

### 10. **Hyphen-Separated Words**
Words with "-" are split, each part titlecased recursively, then rejoined.

**Example Input**: `"state-of-the-art design"`  
**Expected Output**: `"State-of-the-Art Design"`

### 11. **All Consonants (3+ letters) = Acronym**
Words with only consonants and length > 2 are treated as acronyms and uppercased.

**Example Input**: `"html and css and dns"`  
**Expected Output**: `"HTML and CSS and DNS"`

### 12. **Subphrase Capitalization**
After punctuation marks (: ; . ! ? - – ‒ — ―) followed by a space, the next word is capitalized even if it's normally a small word.

**Example Input**: `"chapter one: the beginning"`  
**Expected Output**: `"Chapter One: The Beginning"`

### 13. **Normal Word Capitalization**
Any other word gets its first letter (after optional leading punctuation) capitalized.

**Example Input**: `"hello world"`  
**Expected Output**: `"Hello World"`

## Edge Cases to Test
- Empty strings
- Single small words: `"a"` → `"A"` (first/last rule applies)
- Only punctuation: `"!!!"` → `"!!!"`
- Curly apostrophes vs straight: `"rock 'n' roll"` vs `"rock 'n' roll"`
- Unicode characters: `"éclair and über"` → `"Éclair and Über"`
- Multiple spaces/tabs between words (preserved in output)
- Trailing punctuation: `"end of the world!"` → `"End of the World!"`

## Test Verification Commands

```bash
# Clone and test
git clone https://github.com/ppannuto/python-titlecase
cd python-titlecase

# Test examples
python -c "from titlecase import titlecase; print(titlecase('the lord of the rings'))"
# Expected: The Lord of the Rings

python -c "from titlecase import titlecase; print(titlecase('o\\'neill and d\\'angelo'))"
# Expected: O'Neill and D'Angelo

python -c "from titlecase import titlecase; print(titlecase('state-of-the-art design'))"
# Expected: State-of-the-Art Design
```

## Implementation Notes for Go Port

1. **No regex lookbehind/lookahead**: Go's `regexp` doesn't support these. Use manual string scanning.
2. **Unicode handling**: Use `unicode.ToTitle()` for proper Unicode case conversion.
3. **Preserve whitespace**: Split on whitespace but preserve the exact whitespace characters.
4. **Line-by-line processing**: Read stdin line by line, process each, output with newline.
5. **Recursive calls**: Mc/Mac names, slash-separated, and hyphen-separated words need recursive titlecasing.

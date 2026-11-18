# Notes

## Licence

The MIT License (MIT)

## Rules applied by `titlecase`

1. Blank lines are dropped. A run of carriage returns or line feeds is one line break.
   - Input: `Line number one\n\nand Line three\n`
   - Output: `Line Number One\nAnd Line Three\n`

2. With `preserve_blank_lines=True`, each blank line is kept.
   - Input: `Line number one\n\nand Line three\n`
   - Output: `Line Number One\n\nAnd Line Three\n`

3. Whitespace between words is kept, including tabs and other space characters.
   - Input: `text\twith\ttabs`
   - Output: `Text\tWith\tTabs`

4. With `normalise_space_characters=True`, the words of a line are joined with a single normal space.
   - Input: `text\twith\ttabs`
   - Output: `Text With Tabs`

5. When `callback(word, all_caps=...)` returns a truthy value, that value is the word, and later rules leave it as returned.
   - Input: `a simple tcp and udp wrapper`, with a callback that returns `TCP` and `UDP` for those words
   - Output: `A Simple TCP and UDP Wrapper`

6. On a line with no lowercase letters, a word of dotted initials (`A.` or `A.B`, repeated) stays as written.
   - Input: `WASHINGTON, D.C. SHOULD BE FIXED BUT MIGHT BE A PROBLEM`
   - Output: `Washington, D.C. Should Be Fixed but Might Be a Problem`

7. A word of `d` or `l`, then `'` or `‘`, then letters, with an optional final `'s`, is written with a lowercase first letter and an uppercase letter just after the apostrophe. Characters after that letter stay as they were.
   - Input: `l'grange l'grange l'Grange l'Grange`
   - Output: `l'Grange l'Grange l'Grange l'Grange`

8. The same apostrophe pattern with a leading `o` is written with that `o` and the letter after the apostrophe in uppercase.
   - Input: `my name is o'reilly`
   - Output: `My Name Is O'Reilly`

9. A word that starts with `Mc`, `mc`, or `MC` and then at least two word characters is written as `Mc` plus the titlecased remainder.
   - Input: `oblon, spivak, mcclelland, maier & neustadt`
   - Output: `Oblon, Spivak, McClelland, Maier & Neustadt`

10. A word that is exactly `m`, `mr`, `mrs`, `ms`, or `dr` in any case is written with an uppercase first letter and the remaining characters unchanged.
    - Input: `Mr mr Mrs Ms Mss Dr dr , Mr. and Mrs. Person`
    - Output: `Mr Mr Mrs Ms MSS Dr Dr , Mr. And Mrs. Person`

11. A word that contains a letter, a period, and another letter is left unchanged.
    - Input: `this is just an example.com`
    - Output: `This Is Just an example.com`

12. On a line that already contains a lowercase letter, a word with a capital letter later in the word is left unchanged.
    - Input: `iTunes should be unmolested`
    - Output: `iTunes Should Be Unmolested`

13. These small words are written in lowercase: a, an, and, as, at, but, by, en, for, if, in, of, on, or, the, to, v, v., via, vs, vs. The list is the New York Times Manual of Style list, plus v and vs.
    - Input: `this v that`
    - Output: `This v That`

14. A word that contains `/` and does not contain `//` is split on each slash. Each part is titlecased on its own, and a small word in one of those parts stays lowercase.
    - Input: `a title and/or string`
    - Output: `A Title and/or String`

15. A word that contains `-` is split on each hyphen and each part is titlecased the same way. A small word that is the end of the whole line is still capitalised.
    - Input: `a-b end-to-end two-not-three/three-by-four/five-and`
    - Output: `A-B End-to-End Two-Not-Three/Three-by-Four/Five-And`

16. On a line with no lowercase letters, each remaining word is lowercased before acronym detection and ordinary capitalisation.
    - Input: `THIS IS ALL CAPS AND SHOULD BE ADDRESSED`
    - Output: `This Is All Caps and Should Be Addressed`

17. A word of more than two letters made only of consonants is uppercased. For this test, a, e, i, o, u, and y are vowels.
    - Input: `Words with all consonants like cnn are acronyms`
    - Output: `Words With All Consonants Like CNN Are Acronyms`

18. A consonant-only word of one or two letters is capitalised as an ordinary word.
    - Input: `FOO BAR 5TH ST`
    - Output: `Foo Bar 5th St`

19. Any other word is capitalised on its first letter. Leading punctuation stays in place and the first letter after it is capitalised.
    - Input: `reading between the lines of steve jobs’s ‘thoughts on music’`
    - Output: `Reading Between the Lines of Steve Jobs’s ‘Thoughts on Music’`

20. When the first word character is a digit, that digit is the character this capitalisation sees, so the letters of an ordinal stay lowercase.
    - Input: `34th 3rd 2nd`
    - Output: `34th 3rd 2nd`

21. With `small_first_last=True` (the default), a small word at the start of the line is capitalised, including after leading punctuation. Slash and hyphen parts are processed with this turned off. A word fixed by the callback is left as the callback wrote it.
    - Input: `'by the Way, small word at the start but within quotes.'`
    - Output: `'By the Way, Small Word at the Start but Within Quotes.'`

22. With `small_first_last=True`, a small word at the end of the line is capitalised, including when punctuation follows it.
    - Input: `"Nothing to Be Afraid of?"`
    - Output: `"Nothing to Be Afraid Of?"`

23. A small word that comes right after a subphrase marker and a space is capitalised. The markers are `:`, `.`, `;`, `?`, `!`, `-`, `–`, `‒`, `—`, and `―`.
    - Input: `Starting Sub-Phrase With a Small Word: a Trick, Perhaps?`
    - Output: `Starting Sub-Phrase With a Small Word: A Trick, Perhaps?`

24. Each line is titlecased on its own, and the lines are joined with `\n`.
    - Input: `this shouldn't\nget mangled`
    - Output: `This Shouldn't\nGet Mangled`

# Hand-in: titlecase-go

Task: titlecase-go/ (Harbor task). Rewards: oracle 1.0, nop 0.0, cheat 0.167
(screenshots/). Notes and evidence: NOTES.md.

1. Rules the agent got wrong most: none in the Go port. A one-pass draft
   matched 2000/2000 dev lines and scored 1.0 on the hidden set. The only
   miss was in the agent's rule list: its rule 17 (small word at start of
   line is capitalized) is wrong when the line starts with a space
   (' a thing' -> ' a Thing'), and the list did not mention
   leading/trailing whitespace at all. The hidden set covers it
   (115 hidden lines start with a space).

2. What I would add to make it harder:
   - The pinned commit has no regex look-ahead/behind or back-references,
     so the task is much easier than the brief assumes, and the Python
     source is in the container. Extend the CLI contract (flags for
     small_first_last, preserve_blank_lines, normalise_space_characters,
     multi-line input) so the rules my mutation check found untestable
     (line-breaks, callback, all-caps-initials) become testable.
   - Gate or reweight structure points: a program that compiles with no
     .py files scores 0.33-0.36 without porting anything (cheats B/A,
     deleting .py). Weights 1/1/12 would bring these under 0.2.
   - Grader hardening done: exploits that read the hidden answers or run
     Python scored 1.0 before and 0.0 on behaviour after (jailed binary,
     import rules).
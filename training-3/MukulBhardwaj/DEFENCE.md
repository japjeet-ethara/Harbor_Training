# Day 6 defence

## 0:00–1:30 — What the controls showed

Abhishek's strongest published control uppercased the first ASCII letter of each word and skipped the rest of the titlecase rules. It scored **0.4530** before hardening (`mukul-before-control3`) and **0.0** afterwards (`mukul-after-control3`). Its exact output accuracy fell from 42.95% to 15.99%. In the hardened run it passed build and cleanup, which shows that the accuracy gate was decisive. The optional small-word follow-up was reported at 0.5133 before hardening. Its script was absent from Abhishek's report commit, so I could verify the three published controls.

## 1:30–3:00 — How I changed the grader

The overall reward now stays at zero unless the build passes, the cleanup and smoke check passes, and at least 90% of output lines match byte for byte. The original weighted reward still applies once all three conditions pass. The verifier keeps the individual scores visible so someone can tell whether a submission failed to build or produced wrong answers. I expanded the hidden exam from 2,000 to 100,000 unique titles. The Python reference generated the key twice in standard-library `re` mode. All answers agreed.

| Go port | Wrong on old 2,000 | Wrong on new 100,000 |
| --- | ---: | ---: |
| My original oracle | 0 | 857 |
| Madhur Jain | 0 | 857 |
| Ayush Singh | 0 | 0 |
| My corrected oracle | 0 | 0 |

## 3:00–4:15 — What surprised me

The original oracle passed all 2,000 old cases but failed 857 new ones. The Go port skipped a leading underscore as punctuation, changing `_dream` to `_Dream`. Python's regular expression treats the underscore as a word character and leaves the following letter alone. Checking for a word character before skipping punctuation fixed the Go port. Every exam case stayed in the dataset.

## 4:15–5:00 — Proof at revision 0cda2e8

- Oracle scored **1.0** in `mukul-day5-hardened-oracle-v2`.
- Nop scored **0.0** in `mukul-day6-nop`.
- The three published controls scored **0.0** each in `mukul-after-control1`, `mukul-after-control2`, and `mukul-after-control3`.

All five trials had zero exceptions. The raw oracle and nop rewards and the control scores are in `proof/`.

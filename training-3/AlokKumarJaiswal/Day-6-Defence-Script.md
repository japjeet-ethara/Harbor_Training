# Day 6 defence script

Alok Kumar Jaiswal · titlecase-go · five minutes

## 0:00–1:00 · My strongest Day 4 result

“I worked on titlecase-go, a task that asks for a Go port of a Python titlecasing library. My strongest Day 4 submission against Lokesh’s task was a partial port. It handled interior small words, compounds, all-caps normalization, and dotted initials. Other rules, including the URL exception, were incomplete.

“The verifier reported 0.858 behaviour and awarded 0.905333 overall. The difference came from the separate credit for building successfully and having no Python files. When I ran the same submission against Lokesh’s hardened task in Day 6, it scored zero. His published oracle still scored one.”

## 1:00–2:00 · How I hardened my grader

“My original grader had the same structural scoring problem. A submission could earn about one-third of the total reward from the build and Python cleanup checks alone. I made those checks prerequisites. If either fails, the reward is zero.

“I then squared the raw behaviour score for submissions that pass both checks. Sanyam’s partial port was the strongest submission against my own task. It scored 0.5217 on my original grader, 0.33993 under the linear gate on the expanded exam, and 0.1155524049 under the squared rule, below the assignment’s 0.2 threshold. The raw accuracy stayed the same. The reward changed.”

## 2:00–3:00 · What the bigger exam showed

| Port | Wrong on original 2K | Wrong on official 100K |
|---|---:|---:|
| My final oracle | 0 | 0 |
| Lokesh’s published port | 0 | 3,069 |
| Sanyam’s published port | 0 | 3,053 |

“All three ports passed every line of the original exam. The official 100K exam exposed thousands of differences in the two classmate ports. It changed both the number of titles and the kinds of inputs, so the comparison captures both effects. Diverse cases expose new failure modes. More samples then help catch rare failures within that same input distribution. I generated the answers twice with Python’s standard-library re mode, and all 100,000 agreed byte for byte.”

## 3:00–4:00 · The surprise

“My own oracle initially missed 11,188 titles on the official exam, even though it passed the original one. Every mismatch involved the Unicode thin space, U+2009.

“Python’s reference treats thin space as whitespace. My Go port didn’t split words at that character, so it could miss capitalization later in the title. Once the splitter recognized thin space, the same 100K comparison went from 11,188 mismatches to zero. That was the most useful finding from expanding the exam.”

## 4:00–5:00 · The independent proof

“On my final task, Harbor recorded 1.0 for the oracle and 0.0 for nop. Sanyam independently reran his three original submissions against published revision 395755d. All three scored below 0.2. The strongest retest was Cheat 2 at about 0.1156. His exact Cheat 3 retest scored 0.0001879641, which matched my earlier echo-only control.

“The reports and saved reward files are on training-3. The bigger exam exposed a real correctness problem in my oracle, and the scoring change reduced the reward for the incomplete submissions we tested.”

[Published defence and proof](https://github.com/japjeet-ethara/Harbor_Training/blob/a807ed7/training-3/AlokKumarJaiswal/DEFENCE.md)

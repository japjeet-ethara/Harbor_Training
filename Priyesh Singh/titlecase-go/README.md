# Titlecase Go Harbor Task

## 1. Evaluation Results

| Evaluation | Reward |
| :--- | :---: |
| **Oracle** | `1.0` |
| **Nop** | `0.0` |
| **Cheat** | `0.168` |

The **Oracle** achieved the highest possible reward of `1.0`, while **Nop** scored `0.0` and **Cheat** achieved `0.167`.

---

## 2. Rules Failed Most Often

The following capitalization rules were identified as the most common sources of failure:

* **Sub-phrase Capitalization:** Correctly handling capitalization after Unicode dashes and punctuation marks, including colons (`:`), em dashes (`—`), en dashes (`–`), figure dashes (`‒`), and horizontal bars (`―`).
* **Apostrophe Capitalization:** Distinguishing between apostrophe-based capitalization patterns, such as `l'Grange` and `O'Grange`, while preserving the appropriate naming conventions.
* **Inline Period Preservation:** Preserving periods within text instead of incorrectly interpreting them as sentence boundaries.
* **Mixed-Case Acronyms:** Maintaining the original casing of mixed-case acronyms and abbreviations, particularly when processing entirely uppercase lines.

---

## 3. Hardening Suggestions

The following improvements are recommended to strengthen the implementation and address the identified failure cases.

### 3.1. Implement the Optional Callback Handler
Ensure that the optional callback handler is properly implemented and integrated into the text-processing workflow.

### 3.2. Support Whitespace and Blank-Line Configuration Flags
Implement the following configuration flags:

```go
preserve_blank_lines
normalise_space_characters

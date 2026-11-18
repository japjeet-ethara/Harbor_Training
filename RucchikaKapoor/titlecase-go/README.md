# Titlecase-Go

A Go implementation of the Python `titlecase` library (version 2.4.1), developed as part of a Harbor coding task.

The objective was to port the original Python title-casing functionality to Go while using only the Go standard library and maintaining compatibility with the reference implementation.

## Project Overview

This project converts input text into title case while handling different capitalization rules and special cases, including:

- Standard title capitalization.
- Small words that remain lowercase in the middle of a title.
- Special handling of words at the beginning and end of titles.
- Hyphenated and slash-separated words.
- Apostrophes and possessive forms.
- Names containing prefixes such as `Mc`.
- Titles and abbreviations such as `Mr.`, `Mrs.`, `Ms.`, and `Dr.`.
- Acronyms and words containing periods.
- Preservation of whitespace and input formatting.

The Go implementation follows the processing rules of the original Python reference implementation.

## Technologies Used

- **Go** – Main implementation language.
- **Go Standard Library** – Used for string processing, regular expressions, Unicode handling, and other operations.
- **Python** – Used for the original reference implementation and test utilities.
- **Harbor** – Used to execute and evaluate the coding task.
- **Git and GitHub** – Used for version control and project hosting.

No external Go dependencies are required.

## Project Structure

```text
titlecase-go/
│
├── environment/
│   ├── Dockerfile
│   └── python-titlecase/
│       ├── titlecase/
│       │   ├── __init__.py
│       │   └── tests.py
│       ├── README.rst
│       ├── LICENSE.txt
│       └── ...
│
├── solution/
│   └── solve.sh
│
├── tests/
│   ├── data/
│   │   ├── inputs.txt
│   │   ├── expected.txt
│   │   ├── hidden_inputs.txt
│   │   └── hidden_expected.txt
│   ├── gen.py
│   ├── grade.py
│   └── test.sh
│
├── tools/
│   ├── first_diffs.py
│   ├── make_cheat.py
│   └── run_cheat.sh
│
├── instruction.md
└── task.toml
```

## Implementation Details

The main solution is located in:

`solution/solve.sh`

The script:

1. Sets up the Go project.
2. Creates the Go source code.
3. Implements the title-casing logic using the Go standard library.
4. Removes Python files from the execution repository as required by the task.
5. Builds the Go implementation.

The implementation is designed to reproduce the behavior of the original Python reference while avoiding third-party Go packages.

## Testing and Validation

The project was checked against the provided test cases and evaluated through Harbor.

### Results

| Validation | Result |
|---|---|
| Visible test cases | 2,000 / 2,000 passed |
| Build validation | Passed |
| No-Python validation | Passed |
| Harbor behavior score | 1.000 |
| Harbor overall reward | 1.000 |

The solution successfully completed the Harbor evaluation.

## Harbor Submission

The completed trial was successfully uploaded to Harbor.

- **Task:** titlecase-go
- **Reward:** 1.000
- **Upload status:** Successful

## Purpose

This project demonstrates the process of translating an existing Python implementation into Go, preserving its behavior, handling edge cases, validating the implementation against reference outputs, and completing an automated coding evaluation.

---

**Project:** Titlecase-Go  
**Language:** Go  
**Evaluation platform:** Harbor

# Devansh Sharma — Harbor Practice Task: `titlecase-go`

A Go 1.23 implementation of the original Python `titlecase()` functionality, using only the Go standard library.

The goal is to reproduce the original implementation's output byte-for-byte while satisfying the build, language, and behavioural requirements.

## Results

| Run | Reward | Build | No Python | Behaviour |
|:---|---:|---:|---:|---:|
| **Oracle** | **1.000** | 1.000 | 1.000 | 1.000 |
| **NOP** | **0.000** | 0.000 | 0.000 | 0.000 |
| **Cheat** | **0.1111** | 1.000 | 1.000 | 0.000 |

## Observations

1. **Rules the agent got wrong most:** The cheat implementation passed the build and no-Python checks but failed the behavioural tests because memorising visible expected outputs does not work for hidden test cases.

2. **What would make the task harder:** Add more hidden edge cases covering Unicode, apostrophes, hyphenated words, punctuation, whitespace, and unusual title-casing rules.

## Project Structure

\```text
titlecase-go/
├── cheat/
│   └── solve.sh
├── environment/
│   └── Dockerfile
├── solution/
│   └── solve.sh
├── tests/
│   ├── data/
│   ├── behaviour.py
│   ├── build.py
│   ├── no_python.py
│   ├── Dockerfile
│   ├── reward.toml
│   └── test.sh
├── instruction.md
├── task.toml
└── README.md
\```

## Running the Task

Run the Oracle agent:

\```bash
harbor run -p ./titlecase-go -a oracle
\```

Run the NOP agent:

\```bash
harbor run -p ./titlecase-go -a nop
\```

## Author

**Devansh Sharma**

GitHub: [@devansh-ethara](https://github.com/devansh-ethara)

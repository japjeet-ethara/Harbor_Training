# figlet-go — Task Instruction

## Section 1 — What this task is

Your task is to write a **Go port of pyfiglet's FIGlet rendering engine**.

The reference implementation is the Python library **pyfiglet**, available at:

> https://github.com/pwaller/pyfiglet  
> commit `255827efbc09d662875dad50fa0edc1e1263bf45`

The Go program you write must produce **byte-for-byte identical output** to the original `pyfiglet` for every input string, every font, and every combination of command-line options. No differences in whitespace, newlines, padding, or any other character are permitted.

---

## Section 2 — The Go executable requirements

- The program must be written entirely in **Go**, using the **standard library only**. No third-party packages or modules are permitted.
- It must build cleanly with:
  ```
  go build ./...
  ```
- The compiled binary must be named **`figlet`** and must accept command-line arguments exactly as `pyfiglet` does (see Section 3).
- **No `.py` files may exist anywhere under `/workspace/repo`** when grading runs. Remove or exclude all Python source files before submission.
- All font files the program needs must be **stored inside the repository** (at a path you choose). The program must not download or fetch any font files at runtime.

---

## Section 3 — The eight options the program must support

| Flag | Argument | Description | Default |
|------|----------|-------------|---------|
| `-f` | `<fontname>` | Font to use for rendering | `standard` |
| `-w` | `<width>` | Output width in characters, used for line-wrapping and justification | `80` |
| `-j` | `<justify>` | Justification: `left`, `right`, or `center` | Depends on print direction |
| `-D` | _(none)_ | Set print direction to right-to-left | left-to-right |
| `-r` | _(none)_ | Reverse (mirror) each line of output left-to-right | off |
| `-F` | _(none)_ | Flip the entire output upside down | off |
| `-s` | _(none)_ | Enable smush mode (smush adjacent characters together) | off |
| `-n` | _(none)_ | Render each line of stdin as a separate FIGlet string | off |

All flags must behave exactly as the reference pyfiglet implementation behaves, including edge cases such as interaction between `-r` and `-F`, and the default justification when `-D` is active.

---

## Section 4 — Output rules

- The output of your program must be **byte-for-byte identical** to the output of `python -m pyfiglet` with the same arguments, for every test case.
- Fonts are drawn exclusively from **`pyfiglet/fonts-standard/`** — the standard font set that is already present in the Docker image at `/workspace/repo/pyfiglet/fonts/`. No contributed or external fonts will be tested.
- The program must locate and load its bundled fonts correctly regardless of the **current working directory** from which it is invoked.

---

## Section 5 — Grading and scoring

Grading is **automatic and hidden**. Your score is computed from three components:

| Component | Weight | Description |
|-----------|--------|-------------|
| `build` | 1 | The project compiles successfully with `go build ./...` and produces a `figlet` binary. |
| `no_python` | 1 | No `.py` files exist under `/workspace/repo` and no Python interpreter is invoked at runtime. |
| `behaviour` | 4 | The binary's output matches pyfiglet byte-for-byte across all hidden test cases. |

**Partial scoring** applies within each component:

- A program that builds but produces no output at all scores **1 out of 6**.
- A program that builds and passes some (but not all) behaviour tests scores proportionally between 1/6 and 5/6.
- A **perfect solution** (all components pass fully) scores **1.0**.

The **secret** embedded in this task is revealed only when the `behaviour` component reaches exactly **1.0**.

> Do not attempt to discover, infer, or disclose test case contents, expected outputs, or the secret value.

---

## Section 6 — Explicit exclusions

The following are **strictly forbidden** and will result in a score of zero for the affected component:

- Using any **Python interpreter** or executing any pyfiglet Python code at runtime.
- Using any **third-party Go packages** (all imports must resolve to the Go standard library).
- **Fetching fonts or any other file from the internet** at runtime.
- Reading from `/workspace/repo/pyfiglet/__init__.py` or any other Python source file at runtime.
- Implementing any of the following **out-of-scope options**: colour output (`-c`), font installation (`-L`), font listing (`-l`), or font information (`-i`).

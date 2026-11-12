# practice/inflection-go

A Harbor task: port [inflection](https://github.com/jpvanhal/inflection) 0.5.1, the Python
version of the Rails inflector, to Go with byte-identical output, then remove the Python code.

- What the agent is asked: [instruction.md](instruction.md)
- Author notes, traps and results: [NOTES.md](NOTES.md)

## Run it

With Docker running and `harbor` on PATH, from this folder:

```
python scripts/validate.py
```

It runs three trials and exits 0 only if all pass:

| Trial | What it is | Required reward |
|---|---|---|
| oracle | the reference solution in `solution/` | 1.0 |
| nop | an agent that does nothing | 0.0 |
| cheat | `cheat/solve.sh`, which prints the visible answer sheet | below 0.2 |

## Regenerate the answer sheets

```
python tests/gen.py
```

The output is deterministic, so this must leave `tests/data/` unchanged.

# practice/titlecase-go

A Harbor task: port [python-titlecase](https://github.com/ppannuto/python-titlecase) 2.4.1 to
Go so that the Go program gives byte-identical output, then remove the Python code.

- What the agent is asked: [instruction.md](instruction.md)
- Author notes, rules, traps and results: [NOTES.md](NOTES.md)

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

A single run by hand: `harbor run -p . -a oracle`.

## Regenerate the answer sheets

```
pip install regex
python tests/gen.py
```

The output is deterministic, so this must leave `tests/data/` unchanged.

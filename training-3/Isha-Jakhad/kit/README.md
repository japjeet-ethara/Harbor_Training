# Day 5 exam kit

These are the Day 5 pool, answer-freezing, and comparison scripts. The pool
generator includes additional punctuation, Unicode, number, contraction, and
spacing families so a basic word capitalizer cannot rely on ordinary titles.
`answers.py` and `compare.py` are the trainer kit scripts.

When run from the `Isha-Jakhad` folder, the frozen reference package is at
`../../python-titlecase`. Answers use Python 3.14 with the standard-library
`re` module (`REGEX_AVAILABLE = False`). Run all commands in the same Linux
Python environment so the frozen files use LF line endings. The kit command
sequence is:

```sh
uv run --no-project --python 3.14 python -I kit/make_pool.py 100000 1 pool.txt
uv run --no-project --python 3.14 python -I kit/answers.py ../../python-titlecase pool.txt freeze1
uv run --no-project --python 3.14 python -I kit/answers.py ../../python-titlecase pool.txt freeze2
cmp freeze1/inputs.txt freeze2/inputs.txt
cmp freeze1/answers.txt freeze2/answers.txt
```

Only the frozen `inputs.txt` and `answers.txt` are copied into
`task/tests/data/`; temporary pools and freeze directories are not part of the
submission.

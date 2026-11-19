# kit: Day 5 exam generation (100,000 inputs)

The tools, report and supporting files behind the graded exam in `../task/tests/data/`.
- **Measurements:** the port comparison, the corrected-oracle results and the Harbor rewards
  are in `../measure/README.md`.
- **Not committed:** per the SOP, `pool.txt`, `key/`, `got.txt`, `ports/` and `jobs/`.

## Contents

| Path | What it is |
| --- | --- |
| `make_pool.py`, `make_pool.diff` | Trainer's pool generator, extended with missing word families (diff against the trainer's file) |
| `answers.py` | Trainer's answer freezer, unchanged |
| `compare.py` | Trainer's port comparison, unchanged; used by `../measure/` |
| `report.txt` | `answers.py` report for the 100,000-input exam |
| `tools/families.py` | Word-family classifier used to inspect the old and new exams |
| `tools/check_key.py` | Pairing, uniqueness and recomputation checks for the frozen exam |
| `tools/check_round1_evidence.py` | Confirms that `../task/tests/gen.py` reproduces the retained round-1 exam |
| `evidence/old-exam-2000/` | The round-1 hidden exam, moved here unchanged from `task/tests/data/` |
| `evidence/generation/` | Console logs from generation and checking; the pool log is `pool-log.txt`, because `pool.txt` is git-ignored |
| `.gitattributes` | Keeps every kit file byte for byte |

## Provenance

The trainer kit is `06-kit.zip`, downloaded from Slack on 2026-11-19. The extracted files match
the zip.

| File | Trainer SHA-256 | Here |
| --- | --- | --- |
| `make_pool.py` | `842c07b535e83b78b06747361dbca78809966c8569b3451155c821f66ff6d48e` | extended, see `make_pool.diff` (26 lines added, 0 removed); now `7384a0c19a779a1198e6d44557c3acca6d91e3ec4be30b07ce4cd5a4ef6e4a2a` |
| `answers.py` | `d690b106dd71801fe16e0e3161048fd181607701694224922618b2fccd719fa9` | unchanged |
| `compare.py` | `75a381b06503b18c300909559d2f4c0605a8e1c75c1d8c6be07115a628b3bcf6` | unchanged |

The kit scripts use CRLF line endings, as distributed. The generated data files use LF.

## Original

`ppannuto/python-titlecase` at commit `42f43e2de55bf003b286c6f8e8d8b2d26676a167`
(`v2.4.1-4-g42f43e2`; `__version__ = '2.4.1'`). It was exported with `git archive`, and all 12
files were checked against the commit's blob ids. `titlecase/__init__.py` has SHA-256
`a3d0b99857c7672b9a13ec9df54aa187082be7d39b202dc0511e67e6f7873ef0`, the same as the task's
`environment/repo` copy. It was mounted read-only at `/src`.

## Environment

- Image `ghcr.io/astral-sh/uv@sha256:7cf77f594be8042dab6daa9fe326f90962252268b4f120a7f5dccce4d947e6c1`
  (Debian bookworm), uv 0.9.30, Python 3.14.2 (Unicode 16.0.0), `UV_PYTHON_DOWNLOADS=never`.
- Every step ran as `uv run --no-project --python 3.14 python -I ...`.
- Reference mode: standard-library `re`. The `regex` package is not installed, and the report
  says `regex module used  False`.

## Commands (working directory = this kit's parent)

```sh
uv run --no-project --python 3.14 python -I kit/make_pool.py 100000 1 pool.txt
uv run --no-project --python 3.14 python -I kit/make_pool.py 100000 1 pool-repeat.txt
cmp pool.txt pool-repeat.txt
uv run --no-project --python 3.14 python -I kit/answers.py /src pool.txt key
uv run --no-project --python 3.14 python -I kit/answers.py /src pool.txt key-repeat
cmp key/inputs.txt key-repeat/inputs.txt; cmp key/answers.txt key-repeat/answers.txt
cp key/inputs.txt task/tests/data/inputs.txt; cp key/answers.txt task/tests/data/answers.txt
```

## Results

| Item | Value |
| --- | --- |
| `pool.txt` (both copies identical) | 100,000 unique titles, SHA-256 `779b81d3930a23b0f3af5cf56ef19de29dea3cb632e6aca1fce2a5e20da9606f` |
| Kept / dropped | 100,000 kept, 0 dropped (both freezes) |
| `task/tests/data/inputs.txt` | SHA-256 `779b81d3930a23b0f3af5cf56ef19de29dea3cb632e6aca1fce2a5e20da9606f` (identical to `pool.txt`) |
| `task/tests/data/answers.txt` | SHA-256 `e583966925128443d0fc96d605bed9b486c72463e14b79f66a1add0343ac1b36` |
| `report.txt` | SHA-256 `ecd4f5dae06a3fc2b843c155b833e1162c70f178c3319ff30a5e188681f64376` |
| Second freeze (`key-repeat/`) | byte-identical to `key/` |
| Independent recomputation | 100,000 / 100,000 answers match |
| Answers equal to their input | 2,045 (an echo program scores 0.02045) |
| Same inputs with `regex` installed | 7,701 answers would differ, so the reference mode matters |
| Overlap with the practice set | 1 title (`dr`); 0 with the round-1 hidden exam |

## Data files in the task

| File | Records | SHA-256 | Role |
| --- | ---: | --- | --- |
| `tests/data/inputs.txt` | 100,000 | `779b81d3930a23b0f3af5cf56ef19de29dea3cb632e6aca1fce2a5e20da9606f` | graded exam inputs |
| `tests/data/answers.txt` | 100,000 | `e583966925128443d0fc96d605bed9b486c72463e14b79f66a1add0343ac1b36` | graded exam answers |
| `tests/data/practice_inputs.txt` | 2,000 | `2f086c791fa087200506e0a6eba7dd58517884d5b98ac63dc07e89e62f269052` | visible practice, renamed from `inputs.txt` with its pair |
| `tests/data/practice_expected.txt` | 2,000 | `04afbf845881398322c49da41c8ca658436a5c337ef96a69356d8df3b90232f2` | visible practice, renamed from `expected.txt` with its pair |
| `evidence/old-exam-2000/hidden_inputs.txt` (in this kit) | 2,000 | `017c6ffc7992c0df12185961d24d4ca6266432eebb406c18bcf25e941664e852` | round-1 exam, no longer graded |
| `evidence/old-exam-2000/hidden_expected.txt` (in this kit) | 2,000 | `4dcc8d7b9f0a866fb209de6ba171be07dfe30030d595959315cf1118af1daf9a` | round-1 exam, no longer graded |

`task/tests/gen.py` now writes only the practice pair. Rerun with the pinned original, it wrote
both practice files byte-identically and left `inputs.txt` and `answers.txt` untouched.
`tools/check_round1_evidence.py` confirms that the same generator reproduces both round-1 files
exactly.

## Hash-seed behaviour of `answers.py`

`answers.py` sets `PYTHONHASHSEED=1` for its first child run and `PYTHONHASHSEED=2` for its
second. It also starts each child with `python -I`. `-I` implies `-E`, which makes Python ignore
all `PYTHON*` environment variables, including `PYTHONHASHSEED`. Each child therefore runs with
its own random hash seed, not seeds 1 and 2.

Verified with Python 3.14.2: under `-I` with `PYTHONHASHSEED=1`, `sys.flags.ignore_environment`
is 1 and `sys.flags.hash_randomization` is 1. Two runs printed different `hash("titlecase")`
values; without `-I` they matched.

The stability check is still meaningful: it compares two runs with independent random seeds.
It is just not reproducible seed for seed. `-I` was kept as the SOP requires. `answers.py` was run
twice (four child runs, four random seeds); all agreed, and nothing was dropped.

## Word families added to `make_pool.py`

These families were missing from the old 2,000-title exam. Counts are titles per set (old
practice / old hidden / trainer kit sample / new pool), from
`evidence/generation/families-after.txt`.

| Bank (weight) | Family | old practice | old hidden | trainer kit | new pool |
| --- | --- | ---: | ---: | ---: | ---: |
| `CONTRACTIONS` (3) | typographic apostrophe `’` | 0 | 0 | 0 | 8,160 |
|  | contraction / possessive | 0 | 0 | 2,968 | 14,000 |
| `OUTSIDE_PUNCT` (2), `SYMBOLS` (2) | punctuation or symbol outside titlecase's `PUNCT` | 16 | 10 | 0 | 22,359 |
| `SYMBOLS` | emoji / non-BMP characters | 0 | 0 | 0 | 1,393 |
| `NUMBERS` (3) | no-letter title | 0 | 0 | 0 | 87 |
|  | ordinal (`21st`) | 36 | 38 | 0 | 1,465 |
|  | other letter+digit word (`mp3`, `4k`) | 7 | 14 | 3,041 | 11,924 |
| `SPECIAL_CASE` (2) | case-expanding character (`ﬁ`, `İ`, `ẞ`, `ß`) | 0 | 0 | 1,908 | 8,765 |
| `NONASCII_MIXED` (2) | non-ASCII word with internal capitals | 0 | 0 | 177 | 7,946 |
| `URL_HYPHEN` (1) | URL/path with hyphen, no period | 0 | 0 | 28 | 5,126 |
| `SPACED` (2) | other Unicode space (`　`, ` `, ...) | 0 | 0 | 0 | 7,814 |
|  | zero-width space | 0 | 0 | 0 | 2,092 |

A first attempt that put the new spaces into `SPACES` was discarded as over-weighted (see
`evidence/generation/attempt1-discarded.txt`; its logs are `pool-attempt1-log.txt` and
`families-attempt1.txt`). Cases are kept whether or not any Go port passes them.

## Port comparison

See `../measure/README.md`, which has the source commits, commands, results and evidence. In
short:
- On the 100,000 exam, the original task oracle scored 96,937 and both classmates' ports
  scored 100,000.
- On the round-1 exam, all three scored 2,000.
- The corrected oracle scores 100,000 and 2,000.

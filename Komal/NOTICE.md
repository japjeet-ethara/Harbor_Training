The upstream snapshot in `environment/reference` is python-titlecase 2.4.1,
commit `42f43e2de55bf003b286c6f8e8d8b2d26676a167`, Copyright 2021 Patrick
William Pannuto, distributed under its included MIT license.

The Go implementations were written for these submissions from the upstream
behavior. Candidate implementations were used as comparison baselines, not
copied into the submitted solutions. Unicode tables are generated data from
CPython 3.12.14 and regex 2026.11.9; their generator is included.

This third version shares the verifier, generated Unicode data, and low-level matching/casing helpers with the Kushal version. Its work-stack evaluator, editorial corpus, and nested-name tests are distinct.

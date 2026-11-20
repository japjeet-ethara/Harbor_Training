# Hardening Report

## Holes closed
- **Cheat 1 (Lookup table + fallback):** was `0.417`, now `0.000` (`jobs/2026-11-20__13-26-55`) — fix: gated `build` and `no_python` on real `behaviour` accuracy, and penalized low `behaviour` scores so a weak fallback gets `0.0`.
- **Cheat 2 (Half port):** was `0.417`, now `0.000` (`jobs/2026-11-20__13-27-39`) — fix: gated `build` and `no_python` on `behaviour` and required clean Go stdlib-only code.
- **Cheat 3 (Read hidden answers at runtime):** was `1.000`, now `0.000` (`jobs/2026-11-20__13-28-26`) — fix: isolated the candidate binary by dropping privileges to `nobody` (`uid/gid 65534`) in `/tmp` with a stripped environment so it cannot read `/tests/`.
- **Oracle verification:** `1.000` (`jobs/2026-11-20__13-24-25`).

## Exam: before and after
Old exam: 2,000 inputs | New exam: 100,000 inputs, mode: `re` (WITHOUT `regex`, stated in `instruction.md`)

| Port | Wrong on new exam | Old exam caught it? | Chance 2K random misses it |
|------|------------------:|---------------------|---------------------------:|
| my oracle | 0 | n/a | n/a |
| ShivamTiwari | 3,128 | no | 0% |
| PrashantKumar | 0 | no | 100% |

## What I learned
1. Giving independent points for `build` and `no_python` lets broken or half-ported solutions score over 0.4 without doing real work.
2. Running the candidate binary with root/verifier permissions lets a cheat read `/tests/` directly and score 1.000.
3. Input diversity matters more than raw count: my old 2,000-title exam missed 3,128 bugs in ShivamTiwari's port (like `v1.2` -> `V1.2`) and even missed edge-case bugs in my own oracle that the 100,000-title exam immediately caught.

# Defence Notes (5-Minute Talk)

## 1. Strongest Cheat Against My Task (Before and After)
- **Strongest cheat:** Cheat 3 — Read hidden expected answers at runtime (by PrashantKumar).
- **Score before:** `1.000` (`behaviour 1.0`, `build 1.0`, `no_python 1.0`).
  - *Why it worked:* The verifier ran the candidate binary with full container permissions, so the binary could search `/tests/` at runtime and print the hidden expected answers directly.
- **Score after:** `0.000` (`jobs/2026-11-20__13-28-26`).
  - *How I fixed it:* Dropped privileges to `nobody` (`uid/gid 65534`) in `/tmp` with a stripped environment (`PATH=""`, `HOME="/nonexistent"`) so the candidate binary cannot access `/tests/`.
- **Other cheats (Cheats 1 & 2):** Both dropped from `0.417` to `0.000` (`jobs/2026-11-20__13-26-55` and `jobs/2026-11-20__13-27-39`) by gating `build` and `no_python` on real `behaviour` accuracy and enforcing clean Go stdlib-only code.
- **Final proofs:** Oracle `1.000` (`jobs/2026-11-20__13-24-25`), Nop `0.000` (`jobs/2026-11-20__16-14-42`), all 3 cheats `0.000`.

## 2. Before-and-After Exam Table
Old exam: 2,000 inputs | New exam: 100,000 inputs, mode: `re` (WITHOUT `regex`, stated in `instruction.md`)

| Port | Wrong on new exam | Old exam caught it? | Chance 2K random misses it |
|------|------------------:|---------------------|---------------------------:|
| my oracle | 0 | n/a | n/a |
| ShivamTiwari | 3,128 | no | 0% |
| PrashantKumar | 0 | no | 100% |

## 3. One Thing That Surprised Me
- When I first ran my **own oracle** (which scored `1.000` on my old 2,000-title exam) against the new 100,000-title exam, it only scored **`0.9914`** (`jobs/2026-11-20__13-14-49`)—failing about 860 edge-case titles.
- Fixing those real bugs in `solution/solve.sh` (without removing any inputs) brought my oracle back to **`1.000`**.
- The same 100k exam also caught **3,128 bugs** in ShivamTiwari's port (such as turning `v1.2` into `V1.2`) that my old 2,000-title exam completely missed.

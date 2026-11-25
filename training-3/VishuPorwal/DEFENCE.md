# Defence Presentation — Vishu Porwal / titlecase-go

## 1. Strongest Finding

On the published baseline (`512aba1`), attacker Omar Ghyas demonstrated that the verifier could be completely bypassed via an answer-file access exploit (Cheat 2). Because the original verifier executed arbitrary binaries directly in the grader's environment with full read access to `/tests/data/hidden_expected.txt`, the submitted code was able to read the hidden answer key directly off the filesystem and echo it to stdout, scoring a perfect **`1.0000`** without performing any titlecasing logic.

### Hardened Verifier Defence
To remediate this attack vector, the verifier now builds the submitted Go binary into a freshly provisioned, verifier-owned directory and isolates its runtime execution inside a minimal filesystem jail:
- **Filesystem Isolation:** The program runs via `chroot` in a jail containing only the compiled binary itself. Grader scripts, answer keys (`hidden_expected.txt`), source files, and Python interpreters remain entirely outside the jail root and are physically inaccessible.
- **Unprivileged Runtime:** The binary executes as unprivileged user and group `nobody:nogroup` (`65534:65534`) with all supplementary groups explicitly cleared (`--groups=`), running from `/` with read-only traversability and zero write permissions.
- **I/O Isolation:** Test inputs are streamed exclusively over standard input (`stdin`), outputs are captured from `stdout`/`stderr`, and all other inherited file descriptors are closed (`close_fds=True`).

### Retest Results (Omar Ghyas ATTACK.md at `eb7442c`, Section 11.3)
Tested against commit `231e1a16daf89366446f93be7fcd150c82e0966e`, which shares task tree `d53fe76ddc97106c36baab4574e5f48d4c5427e6` with `091e96b`. *(Note: The original verifier reward JSONs have not been independently checked.)*

All three original Day 4 attacker cheats were neutralized below the `< 0.20` threshold:
- **Cheat 1 (Build + Delete Trick):** Baseline `0.3333` → Hardened **`0.0000`** (Harbor trial path: `jobs/day6-reattack-vishu-cheat1/task__x8heT4m`)
- **Cheat 2 (Read the Exam / Static Answer Leak):** Baseline `1.0000` → Hardened **`0.0000`** (Harbor trial path: `jobs/day6-reattack-vishu-cheat2/task__gqGAPJ5`)
- **Cheat 3 (Python Inside / Subprocess Wrapper):** Baseline `1.0000` → Hardened **`0.0000`** (Harbor trial path: `jobs/day6-reattack-vishu-cheat3/task__d4FuvaQ`)

### Fourth Finding (Open Vulnerability)
Omar identified a fourth attack vector that remains open:
- **Compile-Time Public Exam Embedding (Cheat 4):** The committed exam and answer key were available before runtime isolation. When `network_mode = "public"`, the agent can retrieve the static hidden exam files from GitHub during solve time and embed them at compile time via `//go:embed`, bypassing the `chroot` jail by serving answers entirely from memory.
- **Reported Reward:** **`1.0000`**
- **Harbor Job UUID:** `69f6cfca-6d8f-43aa-abd5-c7c6c5a1cc93` (Trial ID: `task__ZGEpvhq`, trial path: `jobs/day6-reattack-vishu-cheat4/task__ZGEpvhq`)
- **Status:** Open

---

## 2. Exam Comparison

Detailed evaluation records and original verifier artifacts are documented in [measure/RESULTS.md](measure/RESULTS.md).

The exam suite was scaled from the legacy 2,000-title set to a hardened, reproducibly generated 100,000-title suite frozen twice under Python 3.14.10 in standard-library `re` mode (`0` dropped). The comparative saved rewards across the three Go reference ports are:

- **Vishu Porwal:** `1.0000` → `1.0000`
- **Nikhil Choudhary:** `0.9965` → `0.9602`
- **Omar Ghyas:** `1.0000` → `0.9697`

*Note: These comparative measurements predate the verifier's subsequent byte-level comparator fix.*

---

## 3. One Surprise

The most notable surprise emerged from evaluating Omar Ghyas’s Go reference port (`1aea2bf`):
- On the old 2,000-title exam, Omar’s port scored a perfect **`1.0`** (100% match).
- However, when subjected to the comprehensive 100,000-title exam suite, his port missed **3,029 titles**, achieving 96,971 matches out of 100,000 (**`0.9697`**). This demonstrated that the smaller 2,000-title suite failed to exercise subtle edge cases, such as complex punctuation combinations and case transitions, which the 100k exam successfully caught.

### Final 100,000-Title Controls
Following the implementation of the byte-level LF record comparator and strict record-count validation, the final control runs on the 100,000-title exam confirmed the integrity of the grading pipeline:
- **Oracle Control:** **`1.0`** (Harbor Job ID: `003429de-506e-42c0-b09c-bf47bd278d5d`)
- **Nop Control:** **`0.0`** (Harbor Job ID: `c0b520d0-5732-4466-bc6d-28f656f79182`)

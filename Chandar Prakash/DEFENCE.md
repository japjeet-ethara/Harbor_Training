## Five-minute defence

### Strongest cheat

All three original cheats tied at reward `0.18181818181818182`: they each passed the build and no-Python checks while scoring zero behavior. The original lookup script had a stale filename and its 0.0 was not sufficient evidence that the lookup attack was closed: correcting it produced 1.0 by reading the answers during grading. After restricting test-data permissions and running the solution as an unprivileged user, the corrected lookup scored 0.0. The final partial-titlecase re-attack scored `0.07872`; the original lookup and build-only cheats scored `0.0`. Evidence and Harbor job folders are in `proof/cheats-reward.txt`.

### Before-and-after exam

The old 2,000-input measurements showed zero wrong answers for the oracle and both sample ports. On the new 100,000-input suite, the oracle has zero wrong answers, AahanTrikha has 3,900, and RudranshPandey has 28,064. The new suite was frozen without the optional `regex` package; `kit/report.txt` records 100,000 kept and zero dropped.

### What surprised me

The first real Harbor oracle run scored `0.87637`, despite a saved measurement saying the oracle matched every answer. A source comparison found differences between the embedded Go implementation and the measured port. Restoring the measured logic made Harbor reach `1.0`; I kept the difficult inputs rather than weakening the exam. A corrected lookup cheat later scored 1.0 because the verifier ran it with readable answer files; the final fix restricts those files and runs the submission as an unprivileged user.

## Proof

- Oracle reward: `1.0`, `jobs/2026-11-20__17-57-39`.
- No-op reward: `0.0`, `jobs/2026-11-20__17-59-38`.
- Final cheat re-attacks: all below `0.2`; exact scores and job folders are in `proof/cheats-reward.txt`.

The guide requires the Harbor reward files as proof; it does not require screenshots.
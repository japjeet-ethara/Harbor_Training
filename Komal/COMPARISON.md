# Cross-submission audit

Attempted 54 primary submissions; evaluated 52 compiled programs. The original two new programs and the subsequently added Komal program each matched 100,000/100,000 records. Komal was checked against the same frozen audit; candidate programs were not rerun for this addition.

**Scope:** this is a broad Unicode diagnostic, not an official regrading of candidate tasks. Candidates have different reference modes and input contracts. Out-of-contract cases can lower these scores. Solutions were installed into the same pinned Python snapshot; task-specific setup assumptions can affect buildability. Setup failures are listed separately, without algorithmic scores.

Go 1.23.12; CPython 3.12.14; regex 2026.11.9. The stress generator uses seed 841763 and the original Python answer key. One primary solution per participant was selected; a nested duplicate was excluded. Shell line endings were normalized to LF. Execution used containers without network access, a read-only root filesystem, an unprivileged UID and only the program mounted. Source hashes are included; an immutable repository commit was not recorded.

| Submission | Exact agreement | Exit code |
|---|---:|---:|
| Kushal (new) | 100.000% | 0 |
| Hardika (new) | 100.000% | 0 |
| Komal (new) | 100.000% | 0 |
| KumailMujtaba | 100.000% | 0 |
| OmarGhyas | 96.237% | 0 |
| PiyushKhattar | 95.815% | 0 |
| Gunjit | 95.238% | 0 |
| Paniv_Kapoor | 94.548% | 0 |
| BhaveshParihar | 89.667% | 0 |
| AshutoshSharma | 89.667% | 0 |
| AdarshSahani | 89.635% | 0 |
| SatyamPandey | 89.635% | 0 |
| HarshitKumar | 89.634% | 0 |
| AbhishekNain | 88.532% | 0 |
| SaurabhBaghel | 88.068% | 0 |
| MadhurJain | 87.547% | 0 |
| DevanshSharma | 86.145% | 0 |
| MohdRafey | 86.110% | 0 |
| PriyanshuSingh | 86.110% | 0 |
| AkshatTomar | 86.108% | 0 |
| VanamPrashanth-titlecase-go | 85.497% | 0 |
| YashSingla | 84.990% | 0 |
| priya | 84.339% | 0 |
| ayushkhurana | 84.115% | 0 |
| Aman-tiwari-titlecase-go | 84.109% | 0 |
| Isha-Jakhad | 82.777% | 0 |
| Uday-Bhatnagar | 82.776% | 0 |
| ArunBisht | 82.053% | 0 |
| SonuKumar | 82.029% | 0 |
| AnnuKumari | 81.418% | 0 |
| ShubhShukla | 81.417% | 0 |
| TannuKumari | 81.417% | 0 |
| NikhilChoudhary | 81.051% | 0 |
| PragatiSharma | 79.942% | 0 |
| VishuPorwal | 79.942% | 0 |
| GauravSiradhana | 79.915% | 0 |
| Ashishreliable | 78.578% | 0 |
| KushalSoni | 77.097% | 0 |
| Lavesh | 77.096% | 0 |
| AkulMalviya | 76.792% | 0 |
| AyushMishra | 75.703% | 0 |
| Sakshi Singh | 75.539% | 0 |
| Yuvraj-Singh-eGRP2211 | 75.109% | 0 |
| AlokKumarJaiswal | 49.743% | 0 |
| prashant1324task | 49.334% | 0 |
| VanshGupta | 48.618% | 0 |
| SiddharthSingh | 48.296% | 0 |
| RudranshPandey | 48.159% | 0 |
| ShubhamTumane | 36.490% | 0 |
| satvik-tandon | 28.457% | 0 |
| KanishkaSharma | 14.212% | 2 |
| LokeshDeshwal | 9.217% | 0 |
| ShivamTiwari | 8.224% | 0 |
| AyushRanjan-titlecase-go | 0.243% | 2 |
| AyushParasher | 0.000% | 0 |

KumailMujtaba also matched the entire audit. The new submissions tie the best observed functional result; this is not evidence of universal superiority.

## Setup failures

- MohammadAdnan: no testable binary under the common setup; no correctness score is claimed.
- SnehaSadhukhan: no testable binary under the common setup; no correctness score is claimed.

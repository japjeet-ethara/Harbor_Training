# 100,000-record port comparison

All ports received both the original 2,000-record hidden exam (preserved as `old-exam/`) and the new 100,000-record frozen exam (`tests/data/`). Their stdout was compared byte-for-byte by line against each suite's answer file using `kit/compare.py`.

| Port source | Old 2k correct | Old accuracy | New 100k correct | New accuracy |
|---|---:|---:|---:|---:|
| Charitra — `solution/` | 2,000 | 100.000% | 100,000 | 100.000% |
| MadhurJain — `titlecase-go/solution/go` | 1,288 | 64.400% | 91,248 | 91.248% |
| LokeshDeshwal — `titlecase-go/solution` | 698 | 34.900% | 86,753 | 86.753% |

The peers' sources were taken from the checked-out `Harbor_Training` tree; no files in their folders were modified. `measure/run_comparison.sh` runs both suites; `measure/run_old_comparison.sh` runs the original suite alone.

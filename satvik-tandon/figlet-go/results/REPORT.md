# Harbor test results

Final screenshots and Harbor `result.json` files are included in this folder. `go-touch-grass.png` records the Step 8 phrase rendered by the Go program in the Docker room.

| Run | Behaviour | Build | No Python | Reward | Result |
|---|---:|---:|---:|---:|---|
| Oracle (`17:37:49`, before newline fix) | 0.000 | 1.000 | 0.000 | 0.167 | Initial regenerated answers used CRLF line endings. |
| Nop (`17:40:18`) | 0.000 | 0.000 | 0.000 | 0.000 | Expected baseline. |
| Visible-answer cheat (`17:42:07`) | 0.000 | 1.000 | 0.000 | 0.167 | Expected: visible answers did not match hidden cases. |
| Oracle final (`17:46:14`) | 1.000 | 1.000 | 1.000 | 1.000 | Passed on regenerated hidden cases; grader secret unlocked. |
| Oracle recheck (`18:07:55`) | 1.000 | 1.000 | 1.000 | 1.000 | Final repeat run passed. |

The test files contain 2,000 unique visible cases and 2,000 unique hidden cases, with no shared argument lists. The initial oracle mismatch came from Windows CRLF output in the frozen answers; the generator now normalizes captured line endings for Harbor's Linux environment. The final oracle run passed all hidden cases. The separate Step 8 phrase was decoded and rendered by the Go program inside the Docker room, confirming the page secret (`go touch grass`) displays cleanly.

Final evidence files are `oracle-final.*`, `oracle-recheck.result.json`, `nop-final.*`, and `cheat-final.*`, plus `go-touch-grass.png` for Step 8. Earlier screenshots were moved into `archive/` to keep the results folder uncluttered.

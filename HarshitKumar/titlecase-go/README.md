# titlecase-go

This is a Harbor task where an agent ports python-titlecase to Go.

| Run | Reward |
| --- | --- |
| oracle | 1.0 |
| nop | 0.0 |
| cheat | 0.1667 |

The cheat run used a cheat `solve.sh` run with `-a oracle`.

1. Which rules the agent got wrong most: none on behaviour, the Go port matched all 2000 hidden lines on the first try; the only failure was a leftover `titlecase/` directory blocking `go build ./...`, fixed in `solve.sh`.
2. To make it harder: add more URL, email and dash cases, and inputs the original leaves unchanged (right now it changes all 2000 hidden lines).

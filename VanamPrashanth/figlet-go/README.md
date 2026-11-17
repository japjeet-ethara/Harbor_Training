# FigletForge/figlet-go

Harbor task porting `pyfiglet` (Python) to a pure Go implementation in `/workspace/repo`.

## Benchmark Rewards
- **Oracle (`harbor run -p ./figlet-go -a oracle`)**: `1.0` (Build: 1.0, No_Python: 1.0, Behaviour: 1.0; 2,000/2,000 hidden cases passed; secret banner unlocked).
- **Nop (`harbor run -p ./figlet-go -a nop`)**: `0.0` (Build: 0.0, No_Python: 0.0, Behaviour: 0.0).
- **Cheat (`harbor run -p ./figlet-go -a oracle` with `cheat/solve.sh`)**: `0.1667` (< 0.20; Build: 1.0, No_Python: 0.0, Behaviour: 0.0; no secret).

## Honest Lines i hit
- **Smushing Rule Challenge**: Right-to-left (`-D right-to-left`) formatting combined with `-j right` justification and universal overlapping (`smushMode & 63 == 0`), where the dominant foreground character in stream sequence must take precedence over spatial column index.
- **Docker Trap**: `golang:1.23-bookworm` includes Python 3 by default (violating D2), whereas `golang:1.23-alpine` lacks `bash` out-of-the-box (breaking Harbor orchestration), necessitating a pinned Alpine stage with `apk add --no-cache bash`.

## Secrets
- **Task Secret**: `"nice port, human"` rendered in `slant` font upon 100% test completion.
- **Page Secret**: `"go touch grass"` rendered cleanly in `slant` font via `cd /workspace/repo && go build -o /tmp/figlet . && /tmp/figlet -f slant "$(echo Z28gdG91Y2ggZ3Jhc3M= | base64 -d)"`.

# FigletForge/figlet-go

Harbor task porting `pyfiglet` (Python) to a pure Go implementation in `/workspace/repo`.

## Benchmark Rewards
- **Oracle (`harbor run -p ./figlet-go -a oracle`)**: `1.0` (Build: 1.0, No_Python: 1.0, Behaviour: 1.0; 2,000/2,000 hidden cases passed; secret banner unlocked).
- **Nop (`harbor run -p ./figlet-go -a nop`)**: `0.0` (Build: 0.0, No_Python: 0.0, Behaviour: 0.0).
- **Cheat (`harbor run -p ./figlet-go -a oracle` with `cheat/solve.sh`)**: `0.1667` (< 0.20; Build: 1.0, No_Python: 0.0, Behaviour: 0.0; no secret).

## Honest Lines & Challenges Hit
- **Smushing Rule Challenge**: Right-to-left (`-D right-to-left`) formatting combined with `-j right` justification and universal overlapping (`smushMode & 63 == 0`), where the dominant foreground character in stream sequence must take precedence over spatial column index.
- **Docker Trap**: `golang:1.23-bookworm` includes Python 3 by default (violating D2), whereas `golang:1.23-alpine` lacks `bash` out-of-the-box (breaking Harbor orchestration), necessitating a pinned Alpine stage with `apk add --no-cache bash`.

## Rules the Agent Kept Getting Wrong
- **Universal Smushing in RTL (`smushMode & 63 == 0`)**: Overlapping dominance depends on stream direction—in `-D right-to-left`, the left character is rendered later and must override the right character, which the agent inverted.
- **Rule 5 (Big X Smushing - `SM_BIGX = 16`)**: The agent initially smushed both `'<'` + `'>'` and `'>'` + `'<'` into `'X'`, whereas `FigletBuilder` only smushes inward brackets (`'>'` + `'<'` $\to$ `'X'`), leaving `'<'` + `'>'` unsmushed.
- **Rule 4 (Opposite Pair Smushing - `SM_PAIR = 8`)**: The agent smushed identical brackets like `[` + `[` instead of strictly opposing pairs (`[` + `]`, `{` + `}`, `(` + `)`) into `'|'`.
- **Hardblank Smushing (`SM_HARDBLANK = 32`)**: The agent treated hardblanks as regular blank spaces during kerning passes, rather than preserving them as visible sub-characters until output sanitization.

## Secrets
- **Task Secret**: `"nice port, human"` rendered in `slant` font upon 100% test completion.
- **Page Secret**: `"go touch grass"` rendered cleanly in `slant` font via `cd /workspace/repo && go build -o /tmp/figlet . && /tmp/figlet -f slant "$(echo Z28gdG91Y2ggZ3Jhc3M= | base64 -d)"`.

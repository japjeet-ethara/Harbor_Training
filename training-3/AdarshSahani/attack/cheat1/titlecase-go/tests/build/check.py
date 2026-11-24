"""Check 1 (weight 1): `go build ./...` compiles in /workspace/repo."""
import rewardkit as rk

# -o /dev/null: compile-check only. Without it, `go build ./...` writes a binary named after the
# module into the repo root, which collides with the existing `titlecase/` folder (module "titlecase").
rk.command_succeeds("go build -o /dev/null ./...", timeout=300)

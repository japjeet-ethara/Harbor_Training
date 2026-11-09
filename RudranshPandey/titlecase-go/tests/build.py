import rewardkit as rk

rk.command_succeeds("go build ./...", name="build", timeout=180)

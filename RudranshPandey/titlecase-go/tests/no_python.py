import rewardkit as rk

rk.command_succeeds(
    "go build ./... && [ -z \"$(find . -name '*.py' -print -quit)\" ]",
    name="no_python",
    timeout=180,
)

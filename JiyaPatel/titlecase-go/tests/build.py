import subprocess
import rewardkit as rk

res = subprocess.run(["go", "build", "./..."], cwd="/workspace/repo", capture_output=True)
rk.record(res.returncode == 0)

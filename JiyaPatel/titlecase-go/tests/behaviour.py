import subprocess
from pathlib import Path
import rewardkit as rk

repo = Path("/workspace/repo")
data = Path("/tests/data")
bin_path = Path("/tmp/titlecase_bin")

score = 0.0
if subprocess.run(["go", "build", "-o", str(bin_path), "."], cwd=repo, capture_output=True).returncode == 0:
    inp = (data / "hidden_inputs.txt").read_text(encoding="utf-8")
    exp = (data / "hidden_expected.txt").read_text(encoding="utf-8").splitlines()
    run = subprocess.run([str(bin_path)], input=inp, capture_output=True, text=True, timeout=30)
    if run.returncode == 0 and exp:
        out = run.stdout.splitlines()
        score = sum(1 for e, a in zip(exp, out) if e == a) / len(exp)

rk.record(score)

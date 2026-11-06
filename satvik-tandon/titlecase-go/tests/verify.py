"""Separate weighted verifier over build, source removal, and hidden behavior."""
from __future__ import annotations
import json
import subprocess
from pathlib import Path
repo=Path.cwd()
data=Path("/tests/data")
build=subprocess.run(["go","build","./..."],cwd=repo,capture_output=True,text=True)
build_score=1.0 if build.returncode==0 else 0.0
python_score=1.0 if build_score and not any(repo.rglob("*.py")) else 0.0
behaviour=0.0
if build_score:
    run=subprocess.run(["go","run","."],cwd=repo,input=(data/"hidden_inputs.txt").read_text(encoding="utf-8"),capture_output=True,text=True)
    expected=(data/"hidden_expected.txt").read_text(encoding="utf-8").splitlines()
    actual=run.stdout.splitlines() if run.returncode==0 else []
    behaviour=sum(a==b for a,b in zip(actual,expected))/len(expected)
result={"build":build_score,"no_python":python_score,"behaviour":behaviour,"reward":(build_score+python_score+4*behaviour)/6}
Path("/logs/verifier").mkdir(parents=True,exist_ok=True)
Path("/logs/verifier/reward.json").write_text(json.dumps(result),encoding="utf-8")
print(json.dumps(result))
print("cwd=", repo)
print("build_stderr=", build.stderr)

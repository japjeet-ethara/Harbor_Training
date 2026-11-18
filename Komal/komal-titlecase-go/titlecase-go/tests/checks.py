import sys
from pathlib import Path
import rewardkit as rk
from rewardkit import criterion

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _grader import evaluate


@criterion(shared=True, description='go build ./... succeeds')
def build(workspace):
    return evaluate(workspace)['build']


@criterion(shared=True, description='build succeeds and no .py files remain')
def no_python(workspace):
    return evaluate(workspace)['no_python']


@criterion(shared=True, description='exact byte agreement on hidden records')
def behaviour(workspace):
    return evaluate(workspace)['behaviour']


rk.build(weight=1)
rk.no_python(weight=1)
rk.behaviour(weight=4)

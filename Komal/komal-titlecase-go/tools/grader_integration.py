import importlib.util
import json
import os
import pwd
import tempfile
from pathlib import Path

spec = importlib.util.spec_from_file_location('independent_grader', '/tests/_grader.py')
grader = importlib.util.module_from_spec(spec)
spec.loader.exec_module(grader)
user = pwd.getpwnam('runner')
grader.LOGS.mkdir(parents=True, exist_ok=True)
grader.LOGS.chmod(0o700)
results = {}
with tempfile.TemporaryDirectory() as directory:
    temp = Path(directory)
    temp.chmod(0o755)
    for sub in ['home', 'cache', 'gopath', 'bin']:
        path = temp / sub
        path.mkdir()
        os.chown(path, user.pw_uid, user.pw_gid)
    forbidden = grader.execute(['/bin/sh', '-c', 'test ! -r /tests/data/hidden_expected.txt && test ! -r /logs/verifier/reward.json'], temp, temp, 'isolation')
    assert forbidden['returncode'] == 0
    results['runner_cannot_read_answers_or_reward'] = True
    timeout = grader.execute(['/bin/sh', '-c', 'sleep 5'], temp, temp, 'timeout-probe', timeout=.1)
    assert timeout['timed_out'] and timeout['returncode'] != 0
    results['timeout_kills_process_group'] = True
    empty = temp / 'empty'
    empty.mkdir()
    result = grader.grade(empty)
    assert result == dict(build=0.0, no_python=0.0, behaviour=0.0), result
    results['deletion_only_gets_zero'] = True
    candidate = temp / 'candidate'
    candidate.mkdir()
    (candidate / 'go.mod').write_text('module scoring/probe\n\ngo 1.23\n')
    (candidate / 'main.go').write_text('package main\nfunc main() {}\n')
    (candidate / 'left.py').write_text('')
    result = grader.grade(candidate)
    assert result == dict(build=1.0, no_python=0.0, behaviour=0.0), result
    results['build_only_with_python_gets_one_sixth'] = True
    (candidate / 'left.py').unlink()
    result = grader.grade(candidate)
    assert result == dict(build=1.0, no_python=1.0, behaviour=0.0), result
    results['build_and_no_python_get_one_third'] = True
print(json.dumps(results, indent=2))

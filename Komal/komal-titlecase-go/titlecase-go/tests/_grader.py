import functools
import json
import os
import pwd
import resource
import signal
import subprocess
import tempfile
import threading
from pathlib import Path

LOCK = threading.Lock()
RESULTS = {}
HERE = Path(__file__).resolve().parent
LOGS = Path('/logs/verifier')


def compare_output(actual, expected, successful):
    answers = expected[:-1].split(b'\n') if expected.endswith(b'\n') else expected.split(b'\n')
    lines = actual[:-1].split(b'\n') if actual.endswith(b'\n') else actual.split(b'\n')
    if not actual:
        lines = []
    correct = sum(i < len(lines) and line == lines[i] for i, line in enumerate(answers))
    denominator = max(len(answers), len(lines))
    if not successful or (actual and not actual.endswith(b'\n')):
        return 0.0, correct, len(lines)
    return correct / denominator if denominator else 1.0, correct, len(lines)


def child_setup(file_limit):
    user = pwd.getpwnam('runner')
    os.setgroups([])
    os.setgid(user.pw_gid)
    os.setuid(user.pw_uid)
    resource.setrlimit(resource.RLIMIT_CPU, (60, 60))
    resource.setrlimit(resource.RLIMIT_FSIZE, (file_limit, file_limit))
    resource.setrlimit(resource.RLIMIT_NPROC, (256, 256))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))


def execute(args, cwd, temp, label, payload=None, timeout=60):
    env = dict(PATH='/usr/local/go/bin:/usr/local/bin:/usr/bin:/bin', HOME=str(temp / 'home'),
               GOCACHE=str(temp / 'cache'), GOPATH=str(temp / 'gopath'), GOPROXY='off',
               GOSUMDB='off', GOTOOLCHAIN='local', CGO_ENABLED='0', GOMAXPROCS='2', LANG='C.UTF-8')
    stdout, stderr = temp / (label + '.stdout'), temp / (label + '.stderr')
    with stdout.open('wb') as out, stderr.open('wb') as err:
        limit = (128 if label in ('build', 'main-build') else 8) * 1024 * 1024
        process = subprocess.Popen(args, cwd=cwd, env=env, stdin=subprocess.PIPE,
                                   stdout=out, stderr=err, start_new_session=True,
                                   preexec_fn=functools.partial(child_setup, limit))
        timed_out = False
        try:
            process.communicate(payload, timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            os.killpg(process.pid, signal.SIGKILL)
            process.communicate()
    result = dict(command=args, returncode=process.returncode, timed_out=timed_out,
                  stdout=stdout.read_bytes(), stderr=stderr.read_bytes())
    for stream in ['stdout', 'stderr']:
        (LOGS / (label + '.' + stream)).write_bytes(result[stream])
    return result


def evaluate(workspace):
    with LOCK:
        key = str(workspace)
        if key not in RESULTS:
            RESULTS[key] = grade(Path(workspace))
        return RESULTS[key]


def grade(workspace):
    LOGS.mkdir(parents=True, exist_ok=True)
    LOGS.chmod(0o700)
    results = dict(build=0.0, no_python=0.0, behaviour=0.0)
    details = dict(checks=results, weights=dict(build=1, no_python=1, behaviour=4))
    python_files = []
    for parent, dirs, files in os.walk(workspace, followlinks=False):
        python_files.extend(str((Path(parent) / f).relative_to(workspace)) for f in files if f.endswith('.py'))
    details['python_files'] = sorted(python_files)
    with tempfile.TemporaryDirectory(prefix='titlecase-grader-') as directory:
        temp = Path(directory)
        temp.chmod(0o755)
        user = pwd.getpwnam('runner')
        for path in [temp / 'home', temp / 'cache', temp / 'gopath', temp / 'bin']:
            path.mkdir()
            os.chown(path, user.pw_uid, user.pw_gid)
        for parent, dirs, files in os.walk(workspace, followlinks=False):
            os.chown(parent, user.pw_uid, user.pw_gid, follow_symlinks=False)
            for name in files:
                os.chown(Path(parent) / name, user.pw_uid, user.pw_gid, follow_symlinks=False)
        build = execute(['go', 'build', './...'], workspace, temp, 'build')
        details['build_result'] = {k:v for k,v in build.items() if k not in ('stdout', 'stderr')}
        if build['returncode'] == 0 and not build['timed_out']:
            results['build'] = 1.0
            results['no_python'] = float(not python_files)
            executable = temp / 'bin/titlecase'
            compile_main = execute(['go', 'build', '-o', str(executable), '.'], workspace, temp, 'main-build')
            details['main_build_result'] = {k:v for k,v in compile_main.items() if k not in ('stdout', 'stderr')}
            if compile_main['returncode'] == 0 and not compile_main['timed_out']:
                payload = (HERE / 'data/hidden_inputs.txt').read_bytes()
                expected = (HERE / 'data/hidden_expected.txt').read_bytes()
                run = execute([str(executable)], workspace, temp, 'behaviour', payload=payload, timeout=30)
                success = run['returncode'] == 0 and not run['timed_out']
                score, correct, line_count = compare_output(run['stdout'], expected, success)
                results['behaviour'] = score
                details['behaviour_result'] = dict(returncode=run['returncode'], timed_out=run['timed_out'],
                                                   correct=correct, expected_records=2000, actual_records=line_count,
                                                   terminated_by_lf=run['stdout'].endswith(b'\n'))
                answers, actual, inputs = expected[:-1].split(b'\n'), run['stdout'].split(b'\n'), payload[:-1].split(b'\n')
                mismatches = []
                for i, answer in enumerate(answers):
                    got = actual[i] if i < len(actual) else b'<missing>'
                    if got != answer:
                        mismatches.append(dict(index=i, input=repr(inputs[i]), expected=repr(answer), actual=repr(got)))
                        if len(mismatches) == 10:
                            break
                details['mismatches'] = mismatches
    details['weighted_mean'] = (results['build'] + results['no_python'] + 4 * results['behaviour']) / 6
    (LOGS / 'checks.json').write_text(json.dumps(details, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(details, indent=2), flush=True)
    return results

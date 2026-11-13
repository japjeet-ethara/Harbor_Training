import json
import os
import signal
import subprocess
import tempfile
from functools import cache
from pathlib import Path


DATA = Path('/tests/data')
OUTPUT_LIMIT = 8 * 1024 * 1024
BUILD_ENV = {
    'PATH': '/usr/local/go/bin:/usr/local/bin:/usr/bin:/bin',
    'HOME': '/tmp/candidate-home',
    'GOCACHE': '/tmp/candidate-cache',
    'GOMODCACHE': '/tmp/candidate-modules',
    'GOPROXY': 'off',
    'GOSUMDB': 'off',
    'GOTOOLCHAIN': 'local',
    'GOMAXPROCS': '2',
    'CGO_ENABLED': '0',
    'GOFLAGS': '-mod=readonly -buildvcs=false -p=2',
}


def command(arguments, cwd, timeout=180):
    process = subprocess.Popen(
        arguments, cwd=cwd, env=BUILD_ENV, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, user=10001, group=10001, start_new_session=True,
    )
    try:
        stdout, stderr = process.communicate(timeout=timeout)
        return process.returncode, stdout, stderr
    except subprocess.TimeoutExpired:
        return -1, b'', b'time limit exceeded'
    finally:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.wait()


def objects(data):
    decoder = json.JSONDecoder()
    text = data.decode()
    while text.strip():
        text = text.lstrip()
        value, end = decoder.raw_decode(text)
        yield value
        text = text[end:]


@cache
def prepare(workspace):
    workspace = Path(workspace)
    if not workspace.is_dir() or not (workspace / 'go.mod').is_file():
        return False
    for path in [workspace, *workspace.rglob('*')]:
        if path.is_symlink():
            continue
        os.chown(path, 10001, 10001)
    for name in ('candidate-home', 'candidate-cache', 'candidate-modules'):
        path = Path('/tmp') / name
        path.mkdir(exist_ok=True)
        os.chown(path, 10001, 10001)
    try:
        code, _, _ = command(['go', 'build', './...'], workspace)
        if code:
            return False
        code, output, _ = command(['go', 'list', '-deps', '-json', './...'], workspace)
        if code:
            return False
        packages = list(objects(output))
        return bool(packages) and all(
            package.get('Standard') or package.get('Module', {}).get('Main')
            for package in packages
        )
    except (OSError, ValueError):
        return False


def byte_lines(data):
    if data == b'':
        return []
    parts = data.split(b'\n')
    if parts[-1] == b'':
        parts.pop()
        return [line + b'\n' for line in parts]
    return [line + b'\n' for line in parts[:-1]] + [parts[-1]]


def fraction(actual, expected):
    left, right = byte_lines(actual), byte_lines(expected)
    total = max(len(left), len(right))
    if not total:
        return 1.0
    return sum(a == b for a, b in zip(left, right)) / total


def isolated(binary, payload):
    with tempfile.TemporaryDirectory(prefix='titlecase-jail-', dir='/workspace') as folder:
        jail = Path(folder)
        jail.chmod(0o755)
        target = jail / 'filter'
        target.write_bytes(binary.read_bytes())
        target.chmod(0o555)
        with tempfile.TemporaryFile() as stdout, tempfile.TemporaryFile() as stderr:
            process = subprocess.Popen(
                ['/usr/bin/prlimit', '--fsize=' + str(OUTPUT_LIMIT), '--cpu=60', '--nofile=64',
                 '--nproc=128', '--', '/usr/sbin/chroot', '--userspec=10001:10001', folder, '/filter'],
                stdin=subprocess.PIPE, stdout=stdout, stderr=stderr,
                env={'GOMAXPROCS': '2'}, start_new_session=True,
            )
            try:
                process.communicate(payload, timeout=90)
                if process.returncode:
                    stderr.seek(0)
                    Path('/logs/verifier/execution.json').write_text(json.dumps({'exit_code': process.returncode, 'stderr': stderr.read(4096).decode(errors='replace')}))
                    return None
                stdout.seek(0)
                output = stdout.read(OUTPUT_LIMIT + 1)
                return output if len(output) <= OUTPUT_LIMIT else None
            except (subprocess.TimeoutExpired, OSError):
                return None
            finally:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                process.wait()


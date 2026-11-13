import argparse
import json
import os
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from uuid import uuid4
from pathlib import Path


def execute(task, agent, label, destination, config):
    command = ['harbor', 'run', '-p', str(task), '-a', agent, '-o', str(destination), '--job-name', label, '-n', '1']
    if config:
        command.extend(['-c', str(config)])
    environment = dict(os.environ)
    environment['PYTHONPATH'] = str(task) + os.pathsep + environment.get('PYTHONPATH', '')
    result = subprocess.run(command, capture_output=True, text=True, env=environment, cwd=task)
    (destination / f'{label}.terminal.txt').write_text(result.stdout + result.stderr)
    files = list((destination / label).glob('*/verifier/reward.json'))
    if result.returncode or len(files) != 1:
        raise RuntimeError(f'{label}: exit {result.returncode}, reward files {len(files)}\n{result.stdout[-3000:]}\n{result.stderr[-2000:]}')
    scores = json.loads(files[0].read_text())
    print(json.dumps({'run': label, 'scores': scores}), flush=True)
    return scores


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('task', type=Path)
    parser.add_argument('--config', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    task = args.task.resolve()
    if args.config is None:
        args.config = task / 'tools/offline-runtime.json'
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid4().hex[:8]
    output = args.output.resolve() if args.output else task / 'evidence/reruns' / stamp
    output.mkdir(parents=True, exist_ok=False)
    destination = output / 'jobs'
    destination.mkdir()
    scores = {}
    for agent in ('oracle', 'nop'):
        scores[agent] = execute(task, agent, agent, destination, args.config)
    with tempfile.TemporaryDirectory(prefix=task.name + '-cheat-') as folder:
        clone = Path(folder) / task.name
        shutil.copytree(task, clone, ignore=shutil.ignore_patterns('evidence', '__pycache__', '.venv', '.git', '.pytest_cache', 'work'))
        shutil.rmtree(clone / 'solution')
        (clone / 'solution').mkdir()
        shutil.copyfile(task / 'cheat/solve.sh', clone / 'solution/solve.sh')
        shutil.copyfile(task / 'tests/data/expected.txt', clone / 'solution/answers.txt')
        scores['cheat'] = execute(clone, 'oracle', 'cheat', destination, args.config)
    passed = scores['oracle']['reward'] == 1.0 and scores['nop']['reward'] == 0.0 and scores['cheat']['reward'] < .2 and scores['cheat']['build'] == 1.0
    (output / 'baselines.json').write_text(json.dumps({'passed': passed, 'runs': scores}, indent=2) + '\n')
    print(f'Validation results: {output}', flush=True)
    if not passed:
        raise SystemExit('Baseline requirements were not met')


if __name__ == '__main__':
    main()

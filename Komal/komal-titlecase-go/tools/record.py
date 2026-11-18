import argparse
import datetime
import json
import subprocess
import sys
import time
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('name')
parser.add_argument('--cwd', default=None)
parser.add_argument('--timeout', type=int, default=1200)
parser.add_argument('command', nargs=argparse.REMAINDER)
args = parser.parse_args()
command = args.command
if command and command[0] == '--':
    command = command[1:]
root = Path(__file__).resolve().parents[1]
stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
out = root / 'evidence/reruns' / (stamp + '-' + args.name)
out.mkdir(parents=True)
start = time.monotonic()
result = subprocess.run(command, cwd=args.cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=args.timeout)
(out / 'terminal.log').write_bytes(result.stdout)
metadata = dict(command=command, cwd=str(Path(args.cwd or '.').resolve()),
                utc=stamp, exit_code=result.returncode, seconds=time.monotonic()-start)
(out / 'command.json').write_text(json.dumps(metadata, indent=2)+'\n', encoding='utf-8')
print(json.dumps(metadata, indent=2))
sys.stdout.buffer.write(result.stdout)
sys.exit(result.returncode)

import json
import sys
import time
from pathlib import Path

baseline = sys.argv[1]
root = Path('/evidence')
files = list((root / 'jobs' / baseline).glob('*/verifier/reward.json'))
assert len(files) == 1
reward = files[0]
checks = json.loads((reward.parent / 'checks.json').read_text())
print('Komal | Harbor Task 1 | ' + baseline, flush=True)
print('Read-only Linux PTY: actual saved Harbor verifier output', flush=True)
print('Source: ' + str(reward.relative_to(root)), flush=True)
print('reward.json (read directly):', flush=True)
print(reward.read_text(), end='', flush=True)
print('check values read directly from checks.json:', flush=True)
print(json.dumps(checks['checks'], indent=2), flush=True)
if 'behaviour_result' in checks:
    print(json.dumps(checks['behaviour_result'], indent=2), flush=True)
print('Post-run evidence view; source files mounted read-only.', flush=True)
time.sleep(3600)

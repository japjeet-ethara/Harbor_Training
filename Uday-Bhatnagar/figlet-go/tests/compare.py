"""Report the first five output differences on the visible cases."""
import argparse,difflib,json,subprocess
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('binary');a=p.parse_args();bad=0
for line in (Path(__file__).parent/'data/visible.jsonl').read_text().splitlines():
 c=json.loads(line);r=subprocess.run([a.binary,*c['args']],capture_output=True,timeout=5);actual=r.stdout.decode('utf8')
 if r.returncode or actual!=c['out']:
  print('ARGS',repr(c['args']),'EXIT',r.returncode);print(''.join(difflib.unified_diff(c['out'].splitlines(True),actual.splitlines(True),fromfile='expected',tofile='actual')));print(r.stderr.decode('utf8'));bad+=1
  if bad==5:break
print('Differences reported:',bad)

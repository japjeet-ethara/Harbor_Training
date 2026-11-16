"""Assert measured Harbor rewards, never synthesize reward files."""
import json,sys
from pathlib import Path
root=Path(sys.argv[1] if len(sys.argv)>1 else 'jobs')
for mode in ['oracle','nop','cheat']:
 files=list((root/('figlet-'+mode)).glob('**/verifier/reward.json'))
 if len(files)!=1:raise SystemExit(f'{mode}: expected one verifier reward; found {len(files)}')
 d=json.loads(files[0].read_text());r=d['reward']
 assert (r==1 if mode=='oracle' else r==0 if mode=='nop' else r<.2),(mode,d)
 logs=files[0].parent/'test-stdout.txt'
 text=logs.read_text(errors='replace') if logs.exists() else ''
 if mode=='oracle':assert '*** SECRET UNLOCKED ***' in text
 if mode=='cheat':assert 'No secret for you. Yet.' in text and '*** SECRET UNLOCKED ***' not in text
 print(mode,json.dumps(d),str(files[0]))

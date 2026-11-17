"""Freeze upstream main() stdout. Run with --source PATH to the pinned checkout."""
from pathlib import Path
import argparse, contextlib, hashlib, io, json, random, sys

def main():
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,default=Path(__file__).resolve().parents[2]/'pyfiglet');opts=p.parse_args()
 sys.path.insert(0,str(opts.source.resolve()))
 import pyfiglet
 random.seed(7)
 outdir=Path(__file__).parent/'data';outdir.mkdir(exist_ok=True)
 fonts=['standard','slant','small','big','mini','banner','shadow','script']
 texts=['hello','Harbor','Go port','|_|','/\\','\\/','><','[]{}()<>','_ / \\ |','two  spaces','é ß ñ','雪🙂','hello\nworld','a long sentence with many words that must wrap into several lines','', 'A\tB', '   ', '[] []', 'test! 42']
 seen=set();metadata={};font_objects={name:pyfiglet.FigletFont(name) for name in fonts}
 class Capture(io.BytesIO):
  def detach(self):return self
  def write(self,data):return super().write(data.encode() if isinstance(data,str) else data)
 for split in ['visible','hidden']:
  cases=[];attempts=0;rtl_narrow=0
  while len(cases)<2000:
   attempts+=1
   args=['-f',random.choice(fonts),'-w',str(random.choice([10,20,40,60,80,120])),'-j',random.choice(['auto','left','center','right']),'-D',random.choice(['auto','left-to-right','right-to-left'])]
   args += [flag for flag in ['-r','-F','-s','-n'] if random.randrange(4)==0]
   text=random.choice(texts)
   if random.random()<.55:text+=' '+''.join(random.choices('abcXYZ09|_/\\[]{}()<>éßñ',k=random.randint(1,15)))
   args+=['--',text]
   # Upstream loops forever if a glyph exactly fills the width: it wraps
   # without consuming that glyph. Such inputs have no finite stdout oracle.
   if any(font_objects[args[1]].width.get(ord(c),0)>=int(args[3]) for c in text):continue
   key=tuple(args)
   if key in seen:continue
   capture=Capture();old=sys.argv;sys.argv=['pyfiglet']+args
   try:
    with contextlib.redirect_stdout(capture):rc=pyfiglet.main()
   except pyfiglet.CharNotPrinted:
    continue # invalid widths cannot have a successful rendering answer
   finally:sys.argv=old
   if rc not in (None,0):raise RuntimeError(args)
   seen.add(key);cases.append({'args':args,'out':capture.getvalue().decode('utf8')})
   if args[7]=='right-to-left' and int(args[3])<=20:rtl_narrow+=1
  path=outdir/(split+'.jsonl')
  path.write_text(''.join(json.dumps(c,ensure_ascii=True,separators=(',',':'))+'\n' for c in cases),encoding='utf8',newline='\n')
  metadata[split]={'count':len(cases),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'rtl_narrow':rtl_narrow,'attempts':attempts}
 (outdir/'manifest.json').write_text(json.dumps(metadata,indent=2)+'\n',encoding='utf8')
 print(json.dumps(metadata,indent=2))
if __name__=='__main__':main()

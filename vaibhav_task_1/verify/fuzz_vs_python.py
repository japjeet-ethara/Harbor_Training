#!/usr/bin/env python3
"""Extra confidence check: fuzz the oracle's Go port against the original
Python on 70,000 lines (30k generator lines with other seeds + 40k random
character soup from the instruction's alphabet). Needs Go >= 1.23."""
import os, re, sys, random, subprocess, importlib.util, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
solve = open(os.path.join(ROOT, "titlecase-go", "solution", "solve.sh"), encoding="utf-8").read()
src = re.search(r"cat > main.go <<'GOSRC'\n(.*?)\nGOSRC\n", solve, re.S).group(1)
tmp = tempfile.mkdtemp()
open(os.path.join(tmp, "go.mod"), "w").write("module titlecase-go\n\ngo 1.23\n")
open(os.path.join(tmp, "main.go"), "w").write(src)
subprocess.run(["go", "build", "-o", "tc", "."], cwd=tmp, check=True,
               env=dict(os.environ, GOTOOLCHAIN="local", GOPROXY="off"))
BIN = os.path.join(tmp, "tc")
sys.modules['regex']=None
sys.path.insert(0,os.path.join(ROOT,'python-titlecase'))
from titlecase import titlecase
spec=importlib.util.spec_from_file_location('gen',os.path.join(ROOT,'titlecase-go','tests','gen.py'))
gen=importlib.util.module_from_spec(spec); spec.loader.exec_module(gen)
alpha = list("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789") + list("!\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~") + list("“”‘’–‒—―éüñÇÉÜ") + [" "]*12 + ["\t"," "]
lines=[]
for seed in range(2,8):
    r=random.Random(seed)
    for _ in range(5000): lines.append(gen.make_line(r))
r=random.Random(99)
words=gen.NORMAL+gen.SMALL+gen.UC_ELSE+gen.CONSONANT
for _ in range(40000):
    n=r.randint(1,25)
    s="".join(r.choice(alpha) for _ in range(n))
    if r.random()<0.5: s=r.choice(words)+r.choice(" -/:.' ")+s+r.choice(["", " "+r.choice(gen.SMALL)])
    if r.random()<0.2: s=s.upper()
    lines.append(s)
exp=[titlecase(l) for l in lines]
out=subprocess.run([BIN],input="".join(l+"\n" for l in lines).encode(),capture_output=True).stdout.decode().split("\n")[:-1]
bad=[(l,e,a) for l,e,a in zip(lines,exp,out) if e!=a]
print(len(lines),"lines,",len(bad),"diffs", len(out))
for b in bad[:10]: print(b)
sys.exit(1 if bad else 0)

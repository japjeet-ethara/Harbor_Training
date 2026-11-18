"""Differential fuzz: python tools/fuzz.py SEED N /path/to/python-titlecase /path/to/built/go/binary"""
import random,sys,subprocess
sys.path.insert(0,sys.argv[3])
from titlecase import titlecase
random.seed(int(sys.argv[1]))
ALPH=list("aAbBcCdDeElLmMnNoOrRsStTvVxXyY.'‘’-/:;?!, ()[]é É0 1_")+["\t","\u00a0","\u2003","Mc","mc","MC","Dr","mr","vs.","v.","of","the","to","a","and","'s"," ","  ","—","–","“","”","a.b","A."]
N=int(sys.argv[2]); lines=[]
for _ in range(N):
    k=random.randint(1,9)
    s="".join(random.choice(ALPH) for _ in range(k))
    if random.random()<.15: s=s.upper()
    if not s.strip(): s="x"
    lines.append(s)
exp=[titlecase(l) for l in lines]
inp=("\n".join(lines)+"\n").encode()
out=subprocess.run([sys.argv[4]],input=inp,capture_output=True).stdout.decode().split('\n')[:-1]
bad=[(a,b,c) for a,b,c in zip(lines,exp,out) if b!=c]
print("fuzz seed",sys.argv[1],"lines",N,"outlines",len(out),"mismatches",len(bad))
for a,b,c in bad[:8]: print(repr(a),'\n  EXP',repr(b),'\n  GOT',repr(c))

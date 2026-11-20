import os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
MAIN = os.path.join(ROOT, "solution", "main.go")
DATA = os.path.join(HERE, "data")

which = sys.argv[1] if len(sys.argv) > 1 else "visible"
inp = os.path.join(DATA, "inputs.txt" if which == "visible" else "hidden_inputs.txt")
exp = os.path.join(DATA, "expected.txt" if which == "visible" else "hidden_expected.txt")

def read(p):
    a = open(p, encoding="utf-8").read().split("\n")
    if a and a[-1] == "": a.pop()
    return a

lines, want = read(inp), read(exp)
p = subprocess.run(["go", "run", MAIN], input="\n".join(lines) + "\n",
                   capture_output=True, text=True, encoding="utf-8")
if p.returncode != 0:
    print("GO FAILED:\n" + p.stderr[:4000]); sys.exit(1)
got = p.stdout.split("\n")
if got and got[-1] == "": got.pop()

bad = [i for i in range(max(len(want), len(got)))
       if (want[i] if i < len(want) else None) != (got[i] if i < len(got) else None)]
print("set:", which, "| lines:", len(want), "| matched:", len(want)-len(bad),
      "| score:", round((len(want)-len(bad))/len(want), 4))
for i in bad[:10]:
    print("--- line", i+1)
    print("  IN  :", repr(lines[i] if i < len(lines) else None))
    print("  WANT:", repr(want[i] if i < len(want) else None))
    print("  GOT :", repr(got[i] if i < len(got) else None))
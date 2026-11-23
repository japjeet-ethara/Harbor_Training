import hashlib
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
MAIN = os.path.join(ROOT, "solution", "main.go")
DATA = os.path.join(HERE, "data")

which = sys.argv[1] if len(sys.argv) > 1 else "visible"
inp = os.path.join(DATA, "inputs.txt" if which == "visible" else "hidden_inputs.txt")
hashfile = os.path.join(DATA, "expected.sha256.txt" if which == "visible" else "answers.sha256.txt")


def read_lines(p):
    a = open(p, encoding="utf-8").read().split("\n")
    if a and a[-1] == "":
        a.pop()
    return a


def sha(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


lines, want_hash = read_lines(inp), read_lines(hashfile)
p = subprocess.run(["go", "run", MAIN], input="\n".join(lines) + "\n",
                   capture_output=True, text=True, encoding="utf-8")
if p.returncode != 0:
    print("GO FAILED:\n" + p.stderr[:4000])
    sys.exit(1)
got = p.stdout.split("\n")
if got and got[-1] == "":
    got.pop()

bad = [i for i in range(max(len(want_hash), len(got)))
       if (want_hash[i] if i < len(want_hash) else None) != (sha(got[i]) if i < len(got) else None)]
print("set:", which, "| lines:", len(want_hash), "| matched:", len(want_hash) - len(bad),
      "| score:", round((len(want_hash) - len(bad)) / len(want_hash), 4))
for i in bad[:10]:
    print("--- line", i + 1)
    print("  IN  :", repr(lines[i] if i < len(lines) else None))
    print("  GOT :", repr(got[i] if i < len(got) else None))

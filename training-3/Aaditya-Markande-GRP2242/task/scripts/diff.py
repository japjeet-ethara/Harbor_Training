import subprocess, sys

mode = sys.argv[1] if len(sys.argv) > 1 else "visible"
pre = "hidden_" if mode == "hidden" else ""

def rd(p):
    return open(p, encoding="utf-8").read().split("\n")[:-1]

inp = rd(f"/tests/data/{pre}inputs.txt")
exp = rd(f"/tests/data/{pre}expected.txt")
res = subprocess.run(["/tmp/tc_bin"], input="\n".join(inp) + "\n",
                     capture_output=True, text=True, encoding="utf-8")
act = res.stdout.split("\n")[:-1]
print(f"mode={mode} lines: expected={len(exp)} actual={len(act)}")
bad = [i for i in range(len(exp)) if i >= len(act) or act[i] != exp[i]]
for i in bad[:10]:
    print("INPUT:    ", repr(inp[i]))
    print("EXPECTED: ", repr(exp[i]))
    print("ACTUAL:   ", repr(act[i] if i < len(act) else None))
    print()
print(len(bad), "lines differ")
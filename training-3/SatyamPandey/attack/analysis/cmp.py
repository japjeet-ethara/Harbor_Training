"""usage: cmp.py <expected> <got> [show]"""
import sys
def rd(p):
    l = open(p, "rb").read().split(b"\n")
    return l[:-1] if l and l[-1] == b"" else l
e, g = rd(sys.argv[1]), rd(sys.argv[2])
bad = [i for i in range(max(len(e), len(g))) if i >= len(e) or i >= len(g) or e[i] != g[i]]
print(f"lines exp={len(e)} got={len(g)} wrong={len(bad)}")
for i in bad[: int(sys.argv[3]) if len(sys.argv) > 3 else 0]:
    print("  exp:", e[i] if i < len(e) else None, "\n  got:", g[i] if i < len(g) else None)

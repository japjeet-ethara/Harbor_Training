import sys
want = open(sys.argv[1], encoding='utf-8').read().split("\n")[:-1]
got = open(sys.argv[2], encoding='utf-8', errors='replace').read().split("\n")
bad = sum(1 for i, w in enumerate(want) if i >= len(got) or got[i] != w)
print(f"old exam: wrong {bad} of {len(want)} -> {'CAUGHT' if bad else 'NOT caught'}")

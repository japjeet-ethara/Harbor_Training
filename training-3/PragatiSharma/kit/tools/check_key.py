import sys
sys.path.insert(0, "/src")
import titlecase as m

def rec(path):
    b = open(path, "rb").read()
    assert b.endswith(b"\n"), path
    return b, [x.decode("utf-8") for x in b[:-1].split(b"\n")]

bi, ins = rec("key/inputs.txt")
ba, ans = rec("key/answers.txt")
print("mode: REGEX_AVAILABLE =", m.REGEX_AVAILABLE)
print("records: inputs", len(ins), "| answers", len(ans), "| paired", len(ins) == len(ans))
print("unique inputs:", len(set(ins)))
print("CR bytes: inputs", bi.count(b"\r"), "| answers", ba.count(b"\r"))
print("embedded line boundaries: inputs", sum(s.splitlines() != [s] for s in ins), "| answers", sum(s.splitlines() != [s] for s in ans if s))
print("empty answers:", ans.count(""))
recomputed = [m.titlecase(t) for t in ins]
print("independent recomputation matches answers.txt:", sum(a == b for a, b in zip(recomputed, ans)), "/", len(ans))
print("answers that differ from their input:", sum(a != t for a, t in zip(ans, ins)))
print("pool.txt == key/inputs.txt:", open("pool.txt", "rb").read() == bi)

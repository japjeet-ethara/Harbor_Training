"""usage: run_tc.py <titlecase_init.py> <inputs> <outputs>  -- one title per \n line"""
import sys, importlib.util
spec = importlib.util.spec_from_file_location("tc_orig", sys.argv[1])
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
print("regex mode:", m.REGEX_AVAILABLE if hasattr(m, "REGEX_AVAILABLE") else ("regex" in sys.modules), file=sys.stderr)
lines = open(sys.argv[2], "rb").read().split(b"\n")
if lines[-1] == b"": lines.pop()
with open(sys.argv[3], "wb") as f:
    for l in lines: f.write(m.titlecase(l.decode("utf-8")).encode("utf-8") + b"\n")

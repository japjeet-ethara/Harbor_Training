"""Confirm the retained round-1 exam reproduces from tests/gen.py (writes nothing).

Usage: python -I -B check_round1_evidence.py <gen.py> <original_src> <evidence_dir>
"""
import importlib.util
import sys

gen_path, src, evidence = sys.argv[1:4]
sys.argv = [gen_path, src]  # gen.py reads the original's path from argv[1]
spec = importlib.util.spec_from_file_location("gen", gen_path)
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)
tc = gen.load_titlecase()
practice, hidden = gen.build_inputs()
want_in = open(f"{evidence}/hidden_inputs.txt", "rb").read()
want_ex = open(f"{evidence}/hidden_expected.txt", "rb").read()
got_in = ("\n".join(hidden) + "\n").encode()
got_ex = ("\n".join(tc.titlecase(t) for t in hidden) + "\n").encode()
print(f"REGEX_AVAILABLE={tc.REGEX_AVAILABLE}")
print(f"round-1 hidden_inputs reproduced: {got_in == want_in}")
print(f"round-1 hidden_expected reproduced: {got_ex == want_ex}")
sys.exit(0 if got_in == want_in and got_ex == want_ex else 1)

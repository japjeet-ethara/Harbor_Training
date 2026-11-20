import sys
import sys, re
sys.stdout.reconfigure(encoding="utf-8")
lines = open(sys.argv[1], "rb").read().decode("utf-8").split("\n")[:-1]
checks = {
 "digits (v1.2, 3rd)": r"\d", "underscore (_dream)": r"_", "tab": "\t", "non-breaking space": "\u00a0",
 "dotless/dotted i (ıstanbul)": "[ıİ]", "any non-ASCII letter": r"[^\x00-\x7f]", "Mc + hyphen (Mcx-)": r"(?i)mc\w*-",
 "slash (TCP/IP)": "/", "dotted words (v.)": r"\w\.\w|\bv\.", "apostrophe": "['’]",
}
for k, p in checks.items():
    print(f"  {k:30s} {sum(1 for l in lines if re.search(p, l)):6d} / {len(lines)}")
words = set(w.lower() for l in lines for w in re.split(r"[\s]+", l) if w)
print(f"  distinct words (lower-cased)   {len(words):6d}")

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "environment" / "python-titlecase"))
import titlecase as tc

samples = [
    "L'Between — MCFtp — OR — rhythm! — nasa",
    "Francisco-generalissimo-html-WAshingToN",
    "l'iPHONe",
    "l'CNN",
    "OR",
    "— OR",
    "foo — OR",
    "MCFtp — OR",
]
print("SUBPHRASE", tc.SUBPHRASE.pattern)
print("SUB CPS", [hex(ord(c)) for c in tc.SUBPHRASE.pattern])
print("UC", tc.UC_ELSEWHERE.pattern)
print("regex flag", tc.REGEX_AVAILABLE)
s = "foo — OR"
print("SAMPLE CPS", [hex(ord(c)) for c in s])
print("FIND", tc.SUBPHRASE.findall(s))
for s in samples:
    print("---")
    print("IN ", s)
    print("OUT", tc.titlecase(s))
    print("UC match", bool(tc.UC_ELSEWHERE.match(s)), "search", bool(tc.UC_ELSEWHERE.search(s)))
    print("SUB", tc.SUBPHRASE.findall(tc.titlecase(s)))

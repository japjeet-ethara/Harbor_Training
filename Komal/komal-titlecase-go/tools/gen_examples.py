import json
from reference import ROOT, load

ref = load()
samples = [
    'the library of the town', 'THE LIBRARY OF THE TOWN', 'the BBC and the RSPB',
    'A.B.C AND THE FINAL', "d'arcy and o'neill", "O'NEILL AND L'ART'S", 'MCLEOD and mcdonald',
    'McA and Mcab', 'mr mRS ms DR at the hall', 'iPhone and eBay', 'a.b AND THE HALL',
    'bcd and rhythm and st', 'the arts/crafts and mother-in-law', 'the a/b-c/d-e final',
    'https://civic.example/a-b', 'the hall: andante via viaduct', 'the hall: vs. the return',
    'the hall - an event', 'ßeta and ﬃlm', 'ǳUNGLE', 'ΟΣ AND AΣ\u0301', '\u0345Σ and A\u0345Σ',
    'İSTANBUL and ſſſ', '\u0301elm e\u0301va', 'Ⅰ.test and Ⅻ', '“the hall”', 'the!!', 'the_',
    'a\u0345 and and\u200c', '\tthe hall\t', 'the\u00a0hall\u2028and\u2029the\x1cteam',
    '', ' ', 'a\n\nb\r\nc\r', '\n\n', 'THE\n\nthe',
]
rows = [dict(input=s, expected=ref.titlecase(s)) for s in samples]
path = ROOT / 'titlecase-go/solution/internal/format/testdata/examples.json'
path.write_text(json.dumps(rows, ensure_ascii=True, indent=2)+'\n', encoding='utf-8')
print(json.dumps(rows, ensure_ascii=True, indent=2))

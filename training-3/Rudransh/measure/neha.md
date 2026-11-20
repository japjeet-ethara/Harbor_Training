# neha port

## Original 2,000-input exam
wrong answers      4 of 2000
chance a random 2000 suite sees none of them: 0%
  input 'TESTING U.S.A. TODAY: new history'
  want  'TESTING U.S.A. TODAY: New History'
  got   'TESTING U.S.A. ToDAY: New History'
  input 'TESTING U.S.A. TODAY: wild space'
  want  'TESTING U.S.A. TODAY: Wild Space'
  got   'TESTING U.S.A. ToDAY: Wild Space'
  input 'TESTING U.S.A. TODAY: deep mountain'
  want  'TESTING U.S.A. TODAY: Deep Mountain'
  got   'TESTING U.S.A. ToDAY: Deep Mountain'
  input 'TESTING U.S.A. TODAY: quiet princess'
  want  'TESTING U.S.A. TODAY: Quiet Princess'
  got   'TESTING U.S.A. ToDAY: Quiet Princess'

## New 100,000-input exam (mentor 06-kit)
wrong answers      3520 of 100000
chance a random 2000 suite sees none of them: 0%
  input 'v1.2'
  want  'v1.2'
  got   'V1.2'
  input 'mrs. in star“ v1.2\u2009the|'
  want  'Mrs. In Star“ v1.2\u2009The|'
  got   'Mrs. In Star“ V1.2\u2009The|'
  input "to eBay BOOK D'Angelo\xa0o'neil v1.2 WORLD"
  want  "To eBay BOOK d'Angelo\xa0O'Neil v1.2 WORLD"
  got   "To eBay BOOK d'Angelo\xa0O'Neil V1.2 WORLD"
  input 'ISTANBUL JavaScript v1.2. mr‘ — McDonald'
  want  'ISTANBUL JavaScript v1.2. Mr‘ — McDonald'
  got   'ISTANBUL JavaScript V1.2. Mr‘ — McDonald'
  input 'v1.2 mcdonald city McDonald'
  want  'v1.2 McDonald City McDonald'
  got   'V1.2 McDonald City McDonald'

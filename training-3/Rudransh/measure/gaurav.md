# gaurav port

## Original 2,000-input exam
wrong answers      0 of 2000
chance a random 2000 suite sees none of them: 100%

## New 100,000-input exam (mentor 06-kit)
wrong answers      18 of 100000
chance a random 2000 suite sees none of them: 70%
  input "book A.B. ftp://host/file\t_Https://x.org' out-of-date École; Dream"
  want  "Book A.B. Ftp://host/file\t_Https://x.org' Out-of-Date École; Dream"
  got   "Book A.B. Ftp://host/file\t_https://x.org' Out-of-Date École; Dream"
  input 'ON A AN MUSIC U.S. V. BY PDF DREAM]'
  want  'On a an Music U.S. V. By PDF Dream]'
  got   'On a an Music U.S. V. by PDF Dream]'
  input "GAME BUT X.'  LIGHT ‘WAR: V. VS. ДОМ; AS"
  want  "Game but X.'  Light ‘War: V. Vs. Дом; As"
  got   "Game but X.'  Light ‘War: V. vs. Дом; As"
  input "D'ANGELO\u2009ISLAND OCEAN RIVER MCDONALD~ A WAR _INPUT/OUTPUT"
  want  "d'ANGELO\u2009Island Ocean River McDonald~ a War _input/Output"
  got   "d'ANGELO\u2009Island Ocean River McDonald~ a War _input/output"
  input '_TCP/IP'
  want  '_tcp/Ip'
  got   '_tcp/ip'

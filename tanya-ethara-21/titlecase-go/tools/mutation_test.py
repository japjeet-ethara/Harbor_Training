"""Mutation test: inject plausible porting bugs into solution/main.go and report how many hidden
lines each one gets wrong (every mutant must be caught). Equivalent mutants (e.g. the dead
UC_INITIALS X.Y branch) legitimately score 0."""
import subprocess,os,shutil,sys,tempfile
HERE=os.path.dirname(os.path.abspath(__file__)); TASK=os.path.dirname(HERE)
SRC=open(os.path.join(TASK,'solution','main.go')).read()
D=os.path.join(TASK,'tests','data')+'/'
env=dict(os.environ,PATH=os.environ.get('GO_BIN','/opt/go123/go/bin')+':'+os.environ['PATH'])
M=[
("ascii-only \\b/\\w", 'return unicode.IsLetter(r) || unicode.IsMark(r) || unicode.Is(unicode.Nd, r) ||\n\t\tunicode.Is(unicode.Pc, r)', 'return r<128 && (r==95 || r>=48&&r<=57 || r>=65&&r<=90 || r>=97&&r<=122)'),
("curly ’ ” treated as PUNCT", 'const punctChars = "!', 'const punctChars = "’”!'),
("SUBPHRASE requires \\b", 'if i+2+len(ar) <= len(rs) && string(rs[i+2:i+2+len(ar)]) == a {', 'if i+2+len(ar) <= len(rs) && string(rs[i+2:i+2+len(ar)]) == a && boundary(rs, i+2+len(ar)) {'),
("SUBPHRASE case-insensitive", 'string(rs[i+2:i+2+len(ar)]) == a {', 'strings.EqualFold(string(rs[i+2:i+2+len(ar)]), a) {'),
("Mc recursion small_first_last=false", 'return capitalize(g1) + titlecase(g2, true)', 'return capitalize(g1) + titlecase(g2, false)'),
("apostrophe: no curly ‘", "(rs[1] != '\\'' && rs[1] != '‘')", "(rs[1] != '\\'')"),
("acronym len>=2", 'if len(rs) <= 2 {\n\t\treturn false\n\t}\n\tfor _, r := range rs {\n\t\tif !foldIn', 'if len(rs) < 2 {\n\t\treturn false\n\t}\n\tfor _, r := range rs {\n\t\tif !foldIn'),
("split only on ASCII space", 'func isSpace(r rune) bool { return unicode.IsSpace(r) }', 'func isSpace(r rune) bool { return r==32||r==9 }'),
("slash/hyphen only first-level (no recursion flag)", 'parts[i] = titlecase(p, false)\n\t\t}\n\t\treturn strings.Join(parts, "/")', 'parts[i] = titlecase(p, true)\n\t\t}\n\t\treturn strings.Join(parts, "/")'),
("inline period ASCII letters only", 'if isLetter(rs[k]) && rs[k+1] == \'.\' && isLetter(rs[k+2])', 'if rs[k]<128 && isLetter(rs[k]) && rs[k+1] == \'.\' && isLetter(rs[k+2])'),
("UC_INITIALS only 'X.' tokens", 'else if i+2 < len(rs) && isUpper(rs[i+2]) && can(i+3) {\n\t\t\t\tres = true\n\t\t\t}', 'else if false {\n\t\t\t\tres = true\n\t\t\t}'),
("Mr/Dr lowercase the rest", 'return upper(string(rs[0])) + string(rs[1:])', 'return upper(string(rs[0])) + lower(string(rs[1:]))'),

("UC_ELSEWHERE doesn't skip leading punct", 'i := 0\n\tfor i < len(rs) && isPunct(rs[i]) {\n\t\ti++\n\t}\n\tif i >= len(rs) || !isLetter(rs[i]) {\n\t\treturn false\n\t}\n\tfor j', 'i := 0\n\tif i >= len(rs) || !isLetter(rs[i]) {\n\t\treturn false\n\t}\n\tfor j'),
("CAPFIRST doesn't skip punct", 'func capFirst(w string) string {\n\trs := []rune(w)\n\ti := 0\n\tfor i < len(rs) && isPunct(rs[i]) {\n\t\ti++\n\t}', 'func capFirst(w string) string {\n\trs := []rune(w)\n\ti := 0'),
("SMALL_FIRST skips punct prefix", 'func smallFirst(w string) string {\n\trs := []rune(w)\n\ti := 0\n\tfor i < len(rs) && isPunct(rs[i]) {\n\t\ti++\n\t}', 'func smallFirst(w string) string {\n\trs := []rune(w)\n\ti := 0'),
("hyphen handled before slash", None, None),
("all_caps not applied to APOS (lowercase first)", 'rs[2] = []rune(upper(string(rs[2])))[0]', 'rs[2] = []rune(upper(string(rs[2])))[0]; if allCaps { return lower(string(rs)) }'),
("no all-caps lowering", '\tif allCaps {\n\t\tword = lower(word)\n\t\trs = []rune(word)\n\t}', ''),
]
res=[]
for name,a,b in M:
    if a is None: continue
    if a not in SRC: print("PATTERN MISSING:",name); continue
    d=tempfile.mkdtemp()
    open(d+'/main.go','w').write(SRC.replace(a,b,1)); open(d+'/go.mod','w').write('module m\n\ngo 1.23\n')
    r=subprocess.run(['go','build','-o','m','.'],cwd=d,env=env,capture_output=True,text=True)
    if r.returncode: print("BUILD FAIL",name,r.stderr[:200]); continue
    inp=open(D+'hidden_inputs.txt','rb').read()
    o=subprocess.run([d+'/m'],input=inp,capture_output=True).stdout.decode().split('\n')[:-1]
    e=open(D+'hidden_expected.txt',encoding='utf-8').read().split('\n')[:-1]
    miss=sum(x!=y for x,y in zip(o,e))+abs(len(o)-len(e))
    res.append((miss,name))
for miss,name in sorted(res,reverse=True): print(f"{miss:5d} / 2000 wrong  -> {name}")
print("caught:",sum(1 for m,_ in res if m>0),"of",len(res))

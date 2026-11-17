from pathlib import Path
import os,shutil,subprocess
import tempfile, argparse
p=argparse.ArgumentParser();p.add_argument('--go',default='go');p.add_argument('--node',default='node');a=p.parse_args()
t=Path(__file__).resolve().parents[1];r=t;w=Path(tempfile.mkdtemp(prefix='figlet-wasm-'))
shutil.copytree(t/'solution/fonts',w/'fonts',dirs_exist_ok=True)
for n in ['tables.go','go.mod']:shutil.copyfile(t/'solution'/n,w/n)
s=(t/'solution/main.go').read_text();s=s.replace('func main() {','func portMain() {').replace('fmt.Print(s + "\\n")','finalOutput = s + "\\n"')
assert 'finalOutput = s + "\\n"' in s
(w/'main.go').write_text(s)
(w/'validate.go').write_text(r'''package main
import("encoding/json";"os";"fmt";"bufio";"path/filepath")
var finalOutput string
type testCase struct {Args []string `json:"args"`;Out string `json:"out"`}
func main(){results:=map[string]any{};for _,split:=range []string{"visible","hidden"}{f,e:=os.Open(filepath.Join(os.Args[1],"tests/data",split+".jsonl"));if e!=nil{panic(e)};scan:=bufio.NewScanner(f);scan.Buffer(make([]byte,65536),16000000);total,matched:=0,0;diffs:=[]any{};for scan.Scan(){var c testCase;if e:=json.Unmarshal(scan.Bytes(),&c);e!=nil{panic(e)};total++;os.Args=append([]string{"figlet"},c.Args...);finalOutput="";portMain();if finalOutput==c.Out{matched++}else if len(diffs)<5{diffs=append(diffs,map[string]any{"args":c.Args,"expected":c.Out,"actual":finalOutput})}};f.Close();results[split]=map[string]any{"matched":matched,"total":total,"first_differences":diffs};fmt.Printf("%s: %d/%d\n",split,matched,total)};data,_:=json.MarshalIndent(results,"","  ");os.WriteFile(os.Getenv("FIGLET_RESULT"),append(data,'\n'),0644);fmt.Println(string(data))}
'''.replace('results:=map[string]any{};','taskPath:=os.Args[1];results:=map[string]any{};').replace('filepath.Join(os.Args[1],','filepath.Join(taskPath,'))
env=os.environ.copy();env.update(GOOS='js',GOARCH='wasm',GOTOOLCHAIN='local',CGO_ENABLED='0',FIGLET_RESULT=str(t/'evidence/wasm-comparison.json'))
go=Path(shutil.which(a.go) or a.go).resolve()
goro=Path(subprocess.check_output([str(go),'env','GOROOT'],text=True).strip())
runner=goro/'misc/wasm/wasm_exec_node.js'
if not runner.exists(): runner=goro/'lib/wasm/wasm_exec_node.js'
subprocess.run([str(go),'build','-o',str(w/'check.wasm'),'.'],cwd=w,env=env,check=True)
subprocess.run([a.node,str(runner),str(w/'check.wasm'),str(t)],env=env,check=True,timeout=180)

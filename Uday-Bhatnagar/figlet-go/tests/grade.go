package main

import (
 "bufio"
 "bytes"
 "context"
 "encoding/base64"
 "encoding/json"
 "fmt"
 "os"
 "os/exec"
 "path/filepath"
 "strings"
 "time"
)
type Case struct {Args []string `json:"args"`; Out string `json:"out"`}
func run(dir string,timeout time.Duration,name string,args ...string)([]byte,error){ctx,cancel:=context.WithTimeout(context.Background(),timeout);defer cancel();cmd:=exec.CommandContext(ctx,name,args...);cmd.Dir=dir;var out bytes.Buffer;cmd.Stdout=&out;cmd.Stderr=os.Stderr;err:=cmd.Run();return out.Bytes(),err}
func main(){
 repo:=os.Getenv("FIGLET_REPO");if repo=="" {repo="/workspace/repo"};tests:=os.Getenv("FIGLET_TESTS");if tests=="" {tests="/tests"};logs:=os.Getenv("FIGLET_LOGS");if logs=="" {logs="/logs/verifier"};binary:=os.Getenv("FIGLET_BINARY");if binary=="" {binary="/tmp/figlet"}
 build,noPython,behaviour:=0.0,0.0,0.0
 _,err:=run(repo,120*time.Second,"go","build","-o",binary,".");if err==nil {_,err=run(repo,120*time.Second,"go","build","./...")};if err==nil {build=1}
 f,err:=os.Open(filepath.Join(tests,"data","hidden.jsonl"));if err!=nil {panic(err)};defer f.Close();scan:=bufio.NewScanner(f);scan.Buffer(make([]byte,65536),16*1024*1024);total,matched:=0,0
 for scan.Scan(){var c Case;if err:=json.Unmarshal(scan.Bytes(),&c);err!=nil {panic(err)};total++;if build==1 {out,e:=run(os.TempDir(),5*time.Second,binary,c.Args...);if e==nil&&string(out)==c.Out {matched++}}};if err:=scan.Err();err!=nil {panic(err)};if total!=2000 {panic(fmt.Sprintf("expected 2000 cases, got %d",total))};behaviour=float64(matched)/float64(total)
 clean:=true;walkErr:=filepath.WalkDir(repo,func(path string,d os.DirEntry,e error)error{if e!=nil {return e};if strings.HasSuffix(d.Name(),".py") {clean=false};if d.Type()&os.ModeSymlink!=0 {target,e:=filepath.EvalSymlinks(path);if e!=nil{return e};if strings.HasSuffix(target,".py") {clean=false}};return nil});if build==1&&clean&&walkErr==nil&&matched>0 {noPython=1}
 reward:=map[string]float64{"reward":(build+noPython+4*behaviour)/6,"build":build,"no_python":noPython,"behaviour":behaviour};os.MkdirAll(logs,0755);data,_:=json.MarshalIndent(reward,"","  ");if err:=os.WriteFile(filepath.Join(logs,"reward.json"),append(data,'\n'),0644);err!=nil {panic(err)};fmt.Printf("Matched %d/%d hidden cases\n%s\n",matched,total,data)
 if behaviour==1 {encoded,e:=os.ReadFile(filepath.Join(tests,"secret.b64"));if e!=nil {panic(e)};secret,e:=base64.StdEncoding.DecodeString(strings.TrimSpace(string(encoded)));if e!=nil {panic(e)};fmt.Println("*** SECRET UNLOCKED ***");out,e:=run(os.TempDir(),5*time.Second,binary,"-f","slant",string(secret));if e!=nil {panic(e)};fmt.Print(string(out))}else{fmt.Println("No secret for you. Yet.")}
}

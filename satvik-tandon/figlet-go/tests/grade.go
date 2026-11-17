package main

import (
 "bufio"
 "context"
 "encoding/base64"
 "encoding/json"
 "fmt"
 "os"
 "os/exec"
 "path/filepath"
 "time"
)
type testCase struct { Args []string `json:"args"`; Out string `json:"out"` }
func run(args ...string) ([]byte,error) { c,x:=context.WithTimeout(context.Background(),5*time.Second);defer x(); return exec.CommandContext(c,"/tmp/figlet",args...).Output() }
func main(){
 build:=0.0; noPython:=0.0; behaviour:=0.0
 cmd:=exec.Command("go","build","-o","/tmp/figlet",".");cmd.Dir="/workspace/repo";if cmd.Run()==nil{build=1}
 f,e:=os.Open("/tests/data/hidden.jsonl");if e==nil&&build==1{defer f.Close();total,correct:=0,0;s:=bufio.NewScanner(f);s.Buffer(make([]byte,1024),16*1024*1024);for s.Scan(){var tc testCase;if json.Unmarshal(s.Bytes(),&tc)!=nil{continue};total++;got,err:=run(tc.Args...);if err==nil&&string(got)==tc.Out{correct++}};if total>0{behaviour=float64(correct)/float64(total)} }
 if build==1&&behaviour>0 {py:=false;filepath.Walk("/workspace/repo",func(path string,info os.FileInfo,err error)error{if err==nil&&info.Mode().IsRegular()&&filepath.Ext(path)==".py"{py=true};return nil});if !py{noPython=1}}
 reward:=(build+noPython+4*behaviour)/6
 os.MkdirAll("/logs/verifier",0755);out,_:=json.Marshal(map[string]float64{"reward":reward,"build":build,"no_python":noPython,"behaviour":behaviour});os.WriteFile("/logs/verifier/reward.json",out,0644)
 fmt.Printf("build=%.3f no_python=%.3f behaviour=%.3f reward=%.3f\n",build,noPython,behaviour,reward)
 if behaviour==1 {b,_:=os.ReadFile("/tests/secret.b64");msg,_:=base64.StdEncoding.DecodeString(string(b));art,_:=run("-f","slant",string(msg));fmt.Println("*** SECRET UNLOCKED ***");fmt.Print(string(art))}else{fmt.Println("No secret for you. Yet.")}
}

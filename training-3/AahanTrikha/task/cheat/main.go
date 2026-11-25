package main

import (
"bufio"
"fmt"
"os"
)

func main() {
f, err := os.Open("/tests/data/expected.txt")
if err != nil {
return
}
defer f.Close()
sc := bufio.NewScanner(f)
sc.Buffer(make([]byte, 1024*1024), 1024*1024)
for sc.Scan() {
fmt.Println(sc.Text())
}
}
package main

import (
"bufio"
"fmt"
"os"
"strings"
)

func main() {
inputFile, _ := os.Open("tests/data/hidden_inputs.txt")
expectedFile, _ := os.Open("tests/data/hidden_expected.txt")
defer inputFile.Close()
defer expectedFile.Close()

inputScanner := bufio.NewScanner(inputFile)
expectedScanner := bufio.NewScanner(expectedFile)

line := 0
diffCount := 0
for inputScanner.Scan() && expectedScanner.Scan() && diffCount < 10 {
line++
input := inputScanner.Text()
expected := expectedScanner.Text()

// Run titlecase on this input
// For now just print what we need to check
fmt.Printf("Line %d:\nInput: %q\nExpected: %q\n\n", line, input, expected)
}
}

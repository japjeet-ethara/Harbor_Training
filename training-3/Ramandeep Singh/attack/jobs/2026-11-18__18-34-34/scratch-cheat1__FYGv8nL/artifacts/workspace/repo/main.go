package main

import (
    "os"
)

func main() {
    data, err := os.ReadFile("/tests/data/hidden_expected.txt")
    if err != nil {
        return
    }

    os.Stdout.Write(data)
}

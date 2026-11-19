package main

import (
    "os"
)

func main() {
    data, err := os.ReadFile("/tests/data/hidden_expected.txt")
    if err != nil {
        os.Exit(2)
    }

    _, _ = os.Stdout.Write(data)

    // Deliberately return a non-zero exit status.
    os.Exit(1)
}

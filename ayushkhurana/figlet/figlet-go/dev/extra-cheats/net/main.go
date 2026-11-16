package main

import (
	"io"
	"net/http"
	"net/url"
	"os"
)

// asks a web service for the answer
func main() {
	resp, err := http.Get("https://example.invalid/figlet?q=" + url.QueryEscape(os.Args[len(os.Args)-1]))
	if err != nil {
		return
	}
	defer resp.Body.Close()
	io.Copy(os.Stdout, resp.Body)
}

package main

/*
#include <stddef.h>

char *c_title(char *s) {
	int word = 1;
	for (char *p = s; *p; p++) {
		unsigned char c = (unsigned char)*p;
		if (c == ' ' || c == '\t') {
			word = 1;
			continue;
		}
		if (word && c >= 'a' && c <= 'z') {
			*p = (char)(c - 32);
			word = 0;
		} else if (c >= 'A' && c <= 'Z') {
			*p = (char)(c + 32);
		}
	}
	return s;
}
*/
import "C"

import (
	"bufio"
	"fmt"
	"os"
	"unsafe"
)

func main() {
	in := bufio.NewScanner(os.Stdin)
	in.Buffer(make([]byte, 64*1024), 1024*1024)
	out := bufio.NewWriter(os.Stdout)
	defer out.Flush()
	for in.Scan() {
		s := C.CString(in.Text())
		C.c_title(s)
		fmt.Fprintln(out, C.GoString(s))
		C.free(unsafe.Pointer(s))
	}
}

package records

import (
	"bufio"
	"fmt"
	"io"
	"strings"
)

func Run(in io.Reader, out io.Writer, transform func(string) string) error {
	r, w := bufio.NewReader(in), bufio.NewWriter(out)
	for {
		line, err := r.ReadString('\n')
		if err != nil && err != io.EOF {
			return err
		}
		if len(line) > 0 {
			if strings.HasSuffix(line, "\n") {
				line = strings.TrimSuffix(line, "\n")
				line = strings.TrimSuffix(line, "\r")
			}
			if _, e := fmt.Fprintln(w, transform(line)); e != nil {
				return e
			}
		}
		if err == io.EOF {
			return w.Flush()
		}
	}
}

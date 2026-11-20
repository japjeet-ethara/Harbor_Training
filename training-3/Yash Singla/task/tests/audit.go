package main

import (
	"fmt"
	"go/ast"
	"go/parser"
	"go/token"
	"io/fs"
	"os"
	"path/filepath"
	"strconv"
	"strings"
)

var forbiddenImports = map[string]bool{
	"C":       true,
	"embed":   true,
	"os/exec": true,
	"plugin":  true,
	"syscall": true,
	"unsafe":  true,
}

var forbiddenCallNames = map[string]bool{
	"Command":        true,
	"CommandContext": true,
	"Exec":           true,
	"ForkExec":       true,
	"LookPath":       true,
	"StartProcess":   true,
}

var forbiddenDirectives = []string{
	"//go:embed",
	"//go:linkname",
	"//go:cgo_import_dynamic",
	"//go:cgo_import_static",
	"//go:cgo_export_dynamic",
	"//go:cgo_export_static",
}

var forbiddenSourceExtensions = map[string]bool{
	".c":    true,
	".cc":   true,
	".cpp":  true,
	".cxx":  true,
	".h":    true,
	".m":    true,
	".mm":   true,
	".s":    true,
	".syso": true,
}

func inspectGoFile(fset *token.FileSet, path string) error {
	file, err := parser.ParseFile(fset, path, nil, parser.ParseComments|parser.AllErrors)
	if err != nil {
		return fmt.Errorf("%s: cannot parse Go source: %w", path, err)
	}

	for _, spec := range file.Imports {
		importPath, err := strconv.Unquote(spec.Path.Value)
		if err != nil {
			return fmt.Errorf("%s: invalid import path: %w", path, err)
		}
		if forbiddenImports[importPath] {
			return fmt.Errorf("%s: forbidden import %q", path, importPath)
		}
	}

	for _, group := range file.Comments {
		for _, comment := range group.List {
			for _, directive := range forbiddenDirectives {
				if strings.Contains(comment.Text, directive) {
					return fmt.Errorf("%s: forbidden directive %q", path, directive)
				}
			}
		}
	}

	var violation error
	ast.Inspect(file, func(node ast.Node) bool {
		if violation != nil {
			return false
		}
		call, ok := node.(*ast.CallExpr)
		if !ok {
			return true
		}
		selector, ok := call.Fun.(*ast.SelectorExpr)
		if ok && forbiddenCallNames[selector.Sel.Name] {
			violation = fmt.Errorf(
				"%s: forbidden process or runtime call %q",
				path,
				selector.Sel.Name,
			)
		}
		return true
	})
	return violation
}

func inspectWorkspace(root string) error {
	fset := token.NewFileSet()
	return filepath.WalkDir(root, func(path string, entry fs.DirEntry, walkErr error) error {
		if walkErr != nil {
			return walkErr
		}
		if entry.Type()&os.ModeSymlink != 0 {
			return fmt.Errorf("%s: symlinks are not allowed", path)
		}
		if entry.IsDir() {
			return nil
		}

		info, err := entry.Info()
		if err != nil {
			return err
		}
		if !info.Mode().IsRegular() {
			return fmt.Errorf("%s: special files are not allowed", path)
		}

		ext := strings.ToLower(filepath.Ext(path))
		if forbiddenSourceExtensions[ext] {
			return fmt.Errorf("%s: non-Go source or assembly is not allowed", path)
		}
		if ext != ".go" {
			return nil
		}
		return inspectGoFile(fset, path)
	})
}

func main() {
	if len(os.Args) != 2 {
		fmt.Fprintln(os.Stderr, "usage: titlecase-audit WORKSPACE")
		os.Exit(2)
	}
	if err := inspectWorkspace(os.Args[1]); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}

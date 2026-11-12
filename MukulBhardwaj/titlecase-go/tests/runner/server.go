package main

import (
	"bytes"
	"context"
	"crypto/subtle"
	"errors"
	"io"
	"log"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"strconv"
	"strings"
	"syscall"
	"time"
)

const (
	listenAddress  = ":8080"
	workspacePath  = "/workspace/repo"
	maxInputBytes  = 16 << 20
	maxOutputBytes = 64 << 20
	runTimeout     = 60 * time.Second
)

type boundedBuffer struct {
	bytes.Buffer
	limit    int
	exceeded bool
}

func (buffer *boundedBuffer) Write(data []byte) (int, error) {
	remaining := buffer.limit - buffer.Len()
	if remaining <= 0 {
		buffer.exceeded = buffer.exceeded || len(data) > 0
		return len(data), nil
	}

	if len(data) > remaining {
		_, _ = buffer.Buffer.Write(data[:remaining])
		buffer.exceeded = true
		return len(data), nil
	}

	return buffer.Buffer.Write(data)
}

func main() {
	token := os.Getenv("RUNNER_AUTH_TOKEN")
	if token == "" {
		log.Fatal("RUNNER_AUTH_TOKEN is required")
	}

	mux := http.NewServeMux()
	mux.HandleFunc("/healthz", func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodGet {
			http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
			return
		}
		w.WriteHeader(http.StatusNoContent)
	})
	mux.Handle("/run", authorize(token, http.HandlerFunc(runProgram)))

	server := &http.Server{
		Addr:              listenAddress,
		Handler:           mux,
		ReadHeaderTimeout: 5 * time.Second,
		IdleTimeout:       30 * time.Second,
		MaxHeaderBytes:    16 << 10,
	}
	if err := server.ListenAndServe(); !errors.Is(err, http.ErrServerClosed) {
		log.Fatal(err)
	}
}

func authorize(token string, next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		const prefix = "Bearer "
		authorization := r.Header.Get("Authorization")
		if !strings.HasPrefix(authorization, prefix) ||
			subtle.ConstantTimeCompare(
				[]byte(strings.TrimPrefix(authorization, prefix)),
				[]byte(token),
			) != 1 {
			http.Error(w, "unauthorized", http.StatusUnauthorized)
			return
		}
		next.ServeHTTP(w, r)
	})
}

func runProgram(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
		return
	}

	input, err := io.ReadAll(io.LimitReader(r.Body, maxInputBytes+1))
	if err != nil {
		http.Error(w, "could not read input", http.StatusBadRequest)
		return
	}
	if len(input) > maxInputBytes {
		http.Error(w, "input too large", http.StatusRequestEntityTooLarge)
		return
	}

	programPath, err := validateProgramPath(r.Header.Get("X-Program-Path"))
	if err != nil {
		http.Error(w, "invalid program path", http.StatusBadRequest)
		return
	}

	ctx, cancel := context.WithTimeout(r.Context(), runTimeout)
	defer cancel()

	command := exec.CommandContext(ctx, programPath)
	command.Dir = workspacePath
	command.Env = []string{
		"HOME=/tmp",
		"TMPDIR=/tmp",
		"PATH=/usr/bin:/bin",
	}
	command.Stdin = bytes.NewReader(input)
	command.Stderr = io.Discard
	output := &boundedBuffer{limit: maxOutputBytes}
	command.Stdout = output
	command.SysProcAttr = &syscall.SysProcAttr{
		Setpgid: true,
		Credential: &syscall.Credential{
			Uid:    65534,
			Gid:    65534,
			Groups: []uint32{},
		},
	}
	command.Cancel = func() error {
		if command.Process == nil {
			return os.ErrProcessDone
		}
		err := syscall.Kill(-command.Process.Pid, syscall.SIGKILL)
		if errors.Is(err, syscall.ESRCH) {
			return os.ErrProcessDone
		}
		return err
	}

	runErr := command.Run()
	if command.Process != nil {
		killProcessGroup(command.Process.Pid)
	}
	if errors.Is(ctx.Err(), context.DeadlineExceeded) {
		http.Error(w, "program timed out", http.StatusGatewayTimeout)
		return
	}
	if errors.Is(ctx.Err(), context.Canceled) {
		return
	}
	if output.exceeded {
		http.Error(w, "program output too large", http.StatusRequestEntityTooLarge)
		return
	}

	exitCode := 0
	if runErr != nil {
		var exitError *exec.ExitError
		if !errors.As(runErr, &exitError) {
			http.Error(w, "could not run program", http.StatusBadGateway)
			return
		}
		exitCode = exitError.ExitCode()
	}

	w.Header().Set("Content-Type", "application/octet-stream")
	w.Header().Set("X-Program-Exit-Code", strconv.Itoa(exitCode))
	w.WriteHeader(http.StatusOK)
	if _, err := w.Write(output.Bytes()); err != nil {
		log.Printf("could not return program output: %v", err)
	}
}

func validateProgramPath(rawPath string) (string, error) {
	if !filepath.IsAbs(rawPath) {
		return "", errors.New("program path must be absolute")
	}

	root, err := filepath.Abs(workspacePath)
	if err != nil {
		return "", err
	}
	program, err := filepath.Abs(rawPath)
	if err != nil {
		return "", err
	}
	if !isWithin(root, program) {
		return "", errors.New("program path is outside workspace")
	}

	info, err := os.Lstat(program)
	if err != nil {
		return "", err
	}
	if !info.Mode().IsRegular() || info.Mode()&os.ModeSymlink != 0 || info.Mode().Perm()&0111 == 0 {
		return "", errors.New("program must be a regular executable")
	}

	resolved, err := filepath.EvalSymlinks(program)
	if err != nil {
		return "", err
	}
	if !isWithin(root, resolved) {
		return "", errors.New("resolved program path is outside workspace")
	}
	return program, nil
}

func isWithin(root, path string) bool {
	relative, err := filepath.Rel(root, path)
	if err != nil || relative == "." || relative == ".." {
		return false
	}
	return !strings.HasPrefix(relative, ".."+string(os.PathSeparator))
}

func killProcessGroup(pid int) {
	err := syscall.Kill(-pid, syscall.SIGKILL)
	if err != nil && !errors.Is(err, syscall.ESRCH) {
		log.Printf("could not clean candidate process group: %v", err)
	}
}

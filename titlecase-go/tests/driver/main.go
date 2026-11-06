package main

import (
	"encoding/json"
	"fmt"
	"os"
	"strings"

	"titlecase"
)

type callbackSpec struct {
	Kind  string   `json:"kind"`
	Words []string `json:"words"`
	Lines []string `json:"lines"`
	Path  string   `json:"path"`
	Match string   `json:"match"`
	Value string   `json:"value"`
}

type testCase struct {
	ID                           string        `json:"id"`
	Text                         string        `json:"text"`
	UseDefault                   bool          `json:"use_default"`
	SmallFirstLast               bool          `json:"small_first_last"`
	PreserveBlankLines           bool          `json:"preserve_blank_lines"`
	NormaliseSpaceCharacters     bool          `json:"normalise_space_characters"`
	Callback                     *callbackSpec `json:"callback"`
	Expected                     string        `json:"expected"`
}

func main() {
	var input testCase
	if err := json.NewDecoder(os.Stdin).Decode(&input); err != nil {
		fmt.Fprintf(os.Stderr, "decode case: %v\n", err)
		os.Exit(2)
	}
	output, err := run(input)
	if err != nil {
		fmt.Fprintf(os.Stderr, "case %s: %v\n", input.ID, err)
		os.Exit(2)
	}
	if err := json.NewEncoder(os.Stdout).Encode(map[string]string{"output": output}); err != nil {
		fmt.Fprintf(os.Stderr, "encode result: %v\n", err)
		os.Exit(2)
	}
}

func run(input testCase) (string, error) {
	if input.UseDefault {
		return titlecase.Titlecase(input.Text, nil), nil
	}
	opts := titlecase.DefaultOptions()
	opts.SmallFirstLast = input.SmallFirstLast
	opts.PreserveBlankLines = input.PreserveBlankLines
	opts.NormaliseSpaceCharacters = input.NormaliseSpaceCharacters
	if input.Callback != nil {
		callback, cleanup, err := makeCallback(*input.Callback)
		if err != nil {
			return "", err
		}
		if cleanup != nil {
			defer cleanup()
		}
		opts.Callback = callback
	}
	return titlecase.Titlecase(input.Text, &opts), nil
}

func makeCallback(spec callbackSpec) (func(string, bool) string, func(), error) {
	switch spec.Kind {
	case "upper_if":
		words := map[string]struct{}{}
		for _, word := range spec.Words {
			words[strings.ToUpper(word)] = struct{}{}
		}
		return func(word string, _ bool) string {
			upper := strings.ToUpper(word)
			if _, ok := words[upper]; ok {
				return upper
			}
			return ""
		}, nil, nil
	case "upper_all":
		return func(word string, _ bool) string {
			return strings.ToUpper(word)
		}, nil, nil
	case "always_empty":
		return func(string, bool) string { return "" }, nil, nil
	case "exact":
		return func(word string, _ bool) string {
			if word == spec.Match {
				return spec.Value
			}
			return ""
		}, nil, nil
	case "echo_all_caps":
		return func(_ string, allCaps bool) string {
			if allCaps {
				return "ALL"
			}
			return ""
		}, nil, nil
	case "wordlist":
		file, err := os.CreateTemp("", "titlecase-wordlist-*.txt")
		if err != nil {
			return nil, nil, err
		}
		for _, line := range spec.Lines {
			if _, err := fmt.Fprintln(file, line); err != nil {
				file.Close()
				os.Remove(file.Name())
				return nil, nil, err
			}
		}
		if err := file.Close(); err != nil {
			os.Remove(file.Name())
			return nil, nil, err
		}
		callback := titlecase.NewWordlistCallback(file.Name())
		return callback, func() { os.Remove(file.Name()) }, nil
	case "wordlist_missing":
		return titlecase.NewWordlistCallback(spec.Path), nil, nil
	default:
		return nil, nil, fmt.Errorf("unknown callback kind %q", spec.Kind)
	}
}

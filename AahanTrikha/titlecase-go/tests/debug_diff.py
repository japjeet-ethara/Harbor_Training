#!/usr/bin/env python3
"""Debug script to find differences between expected and actual output"""

import subprocess
import sys
from pathlib import Path

REPO = Path("/workspace/repo")
DATA = Path("/tests/data")

def main():
    # Build the Go program
    result = subprocess.run(
        ["go", "build", "-o", "/tmp/titlecase-bin", "."],
        cwd=REPO,
        capture_output=True
    )
    
    if result.returncode != 0:
        print("Build failed!")
        return
    
    # Run it
    with open(DATA / "hidden_inputs.txt", "rb") as f:
        inputs_data = f.read()
    
    result = subprocess.run(
        ["/tmp/titlecase-bin"],
        input=inputs_data,
        capture_output=True,
        cwd=REPO
    )
    
    if result.returncode != 0:
        print("Execution failed!")
        return
    
    # Compare outputs
    inputs = (DATA / "hidden_inputs.txt").read_text().splitlines()
    expected = (DATA / "hidden_expected.txt").read_text().splitlines()
    actual = result.stdout.decode().splitlines()
    
    diffs = []
    for i, (inp, exp, act) in enumerate(zip(inputs, expected, actual), 1):
        if exp != act:
            diffs.append((i, inp, exp, act))
            if len(diffs) <= 20:  # Show first 20
                print(f"\nLine {i}:")
                print(f"  Input:    {inp!r}")
                print(f"  Expected: {exp!r}")
                print(f"  Actual:   {act!r}")
    
    print(f"\n{'='*60}")
    print(f"Total lines: {len(inputs)}")
    print(f"Differences: {len(diffs)}")
    print(f"Accuracy: {(len(inputs) - len(diffs)) / len(inputs) * 100:.2f}%")

if __name__ == "__main__":
    main()

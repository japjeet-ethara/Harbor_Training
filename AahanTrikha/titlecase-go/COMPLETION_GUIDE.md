# Titlecase-Go Task - Completion Guide

## Current Status: 99.57% Complete (MUST REACH 100%)

### Completed ✅
- [x] **Step 1**: NOTES.md created with 13 rules and examples
- [x] **Step 2**: Dockerfile exists and builds
- [x] **Step 3**: instruction.md exists
- [x] **Step 4**: Test data exists (inputs/expected files)
- [x] **Step 5**: Tests work with RewardKit
- [ ] **Step 6**: Oracle score = **0.9957** ❌ **MUST BE 1.0**
- [ ] **Step 7**: Nop and cheat tests
- [ ] **Step 8**: Push and document

## CRITICAL: Fix Oracle to 1.0

### What's Wrong
- **13 out of 2000 test cases failing** (99.57% = 0.9957 score)
- Score calculation: (1×build + 1×no_python + 4×behaviour) / 6 = 0.9957
- Behaviour score ≈ 0.99355 → ~13 failures

### How to Find Failures

**Option A: Run Harbor and check debug output**
```powershell
cd c:\Users\AahanTrikha\Desktop\AahanTrikha\titlecase-go
uvx harbor run -p . -a oracle

# Then check:
# jobs\<latest-timestamp>\<trial-id>\verifier\test-stderr.txt
```

The debug script I added will print the first 20 failing cases.

**Option B: Manual debugging** (if Harbor fails)
```powershell
# 1. Build the Go program from solution
cd c:\Users\AahanTrikha\Desktop\AahanTrikha\titlecase-go
bash solution\solve.sh  # This creates Go files

# 2. Run comparison
cd environment\python-titlecase  # or wherever repo is
python -c "
from titlecase import titlecase
import sys
sys.path.insert(0, '../..')

# Test specific cases
test_cases = [
    'the',  # Single small word
    'of',   # Another small word  
    'a tale of two',  # Ends with small word
    'chapter one: the beginning',  # Subphrase
    'o\\'neill',  # Apostrophe pattern
    'mcdonald',  # Mc name
    '',  # Empty
]

for case in test_cases:
    result = titlecase(case)
    print(f'{case!r} → {result!r}')
"
```

### Common Issues to Check in Go Code

Based on the 13 failures, likely culprits:

1. **Empty Line Handling**
   - Check: Does `main()` handle empty lines correctly?
   - Python: Empty lines become empty output lines
   - Go bug: Might skip empty lines or add extra newlines

2. **Trailing Punctuation with Small Words**
   - Check: `smallLast()` function
   - Example: `"end of the."` → Should capitalize "the" if last word
   - Bug: Might not detect if punctuation at end

3. **Unicode Edge Cases**
   - Check: `unicode.ToTitle()` vs `unicode.ToUpper()`
   - Example: Some Unicode chars have different Title vs Upper case
   - Bug: Using wrong function

4. **Apostrophe Variants**
   - Check: `aposSecond()` function  
   - Python checks: `'` (U+0027) and `'` (U+2018)
   - Bug: Might only check one type

5. **Mc/Mac Recursive Calls**
   - Check: `mcName()` function
   - Bug: `return pyCap(prefix) + titlecase(string(r[2:]), true), true)`
   - Second parameter should be `false` not `true`!

6. **Empty Parts in Split**
   - Check: Slash and hyphen splitting
   - Example: `"a/-/b"` → Creates empty part
   - Bug: Might crash or produce wrong output

### Fix Process

1. **Run Harbor once** to get debug output
2. **Identify pattern** in the 13 failures
3. **Fix ONE issue at a time**
4. **Re-run Harbor** after each fix
5. **Repeat until 1.0**

### Most Likely Fix

Looking at the Go code, I suspect the issue is in **`mcName()`**:

```go
// WRONG (current):
return pyC

ap(prefix) + titlecase(string(r[2:]), true), true

// CORRECT (should be):
return pyCapprefix) + titlecase(string(r[2:]), false), true
```

The second parameter to recursive `titlecase()` calls should be `false` to disable `smallFirstLast` for recursive calls.

## After Reaching 1.0

### Step 7: Nop and Cheat Tests

**A. Test Nop Agent**
```powershell
uvx harbor run -p . -a nop
# Must score exactly 0.0
# If not, tests are giving free points
```

**B. Create Cheat Solution**
Create `cheat/solve.sh`:
```bash
#!/bin/bash
set -euo pipefail
cd /workspace/repo

cat > go.mod <<'EOF'
module titlecase-go
go 1.23
EOF

cat > main.go <<'EOF'
package main
import ("bufio"; "fmt"; "os")
func main() {
    lines := []string{
        // Copy FIRST FEW lines from tests/data/expected.txt here as example
        "The Lord of the Rings",
        "A Tale of Two Cities",
        // ... (cheat only has visible set, not hidden)
    }
    for _, line := range lines {
        fmt.Println(line)
    }
}
EOF

find /workspace/repo -type f -name '*.py' -delete
go build ./...
```

**C. Test Cheat**
```powershell
# Backup real solution
Copy-Item solution\solve.sh solution\solve.sh.backup

# Use cheat
Copy-Item cheat\solve.sh solution\solve.sh

# Run
uvx harbor run -p . -a oracle

# Should score < 0.2 (fails on hidden inputs)

# Restore
Move-Item -Force solution\solve.sh.backup solution\solve.sh
```

### Step 8: Submission

1. **Take screenshots** of:
   - Oracle run showing 1.000
   - Nop run showing 0.000  
   - Cheat run showing < 0.200

2. **Push to GitHub**
```powershell
cd c:\Users\AahanTrikha\Desktop\AahanTrikha\titlecase-go
git init
git add .
git commit -m "Complete titlecase-go Harbor task"
git remote add origin <your-repo-url>
git push -u origin main
```

3. **Create summary document** with:
   - Which rules agents got wrong most (based on your iterations)
   - What would make task harder (suggestions: Unicode edge cases, more Mc variations, nested slashes/hyphens)

## Quick Reference Commands

```powershell
# Run oracle
uvx harbor run -p . -a oracle

# Check latest result
$latest = Get-ChildItem jobs -Directory | Sort-Object LastWriteTime -Descending | Select-Object -First 1
Get-Content "$($latest.FullName)\result.json" | ConvertFrom-Json | Select-Object -ExpandProperty stats | Select-Object -ExpandProperty evals

# View debug output
Get-Content "$($latest.FullName)\*\verifier\test-stderr.txt"
```

## Success Criteria Checklist

- [ ] NOTES.md exists with 13+ rules ✅
- [ ] Oracle = 1.000 ❌ (currently 0.9957)
- [ ] Nop = 0.000
- [ ] Cheat < 0.200
- [ ] GitHub repo with screenshots
- [ ] Summary of common agent mistakes

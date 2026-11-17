# Titlecase-Go Task Status

## Current State

### What's Working ✅
- **Tests run successfully**: RewardKit tests execute without errors
- **Reward file created**: `/logs/verifier/reward.json` is generated correctly  
- **Build passes**: Go code compiles successfully
- **No Python files**: All .py files are removed from workspace
- **High accuracy**: **99.57%** of test cases pass (0.9957 score)

### Critical Issue ❌
- **Oracle score: 0.9957** (Must be 1.0 to proceed)
- Approximately **13 out of 2000 test cases** are failing
- Cannot identify which specific test cases fail without interactive debugging

## What Was Fixed
1. ✅ Renamed `gen.py` to `gen.py.bak` (was causing ModuleNotFoundError during test import)
2. ✅ Updated `test.sh` to properly write reward.json using `tee`
3. ✅ Verifier runs in separate environment mode

## What Needs To Be Done

### Immediate (Step 6 - Get Oracle to 1.0)
1. **Find failing test cases**:
   - Run the debug script added to `tests/debug_diff.py`
   - Harbor run should now show first 20 failing lines in stderr
   - Document the patterns of failures

2. **Fix the Go implementation**:
   - Analyze failure patterns  
   - Fix edge cases in the titlecase logic
   - Common issues to check:
     - Unicode handling (unicode.ToTitle vs ToUpper)
     - Apostrophe variants (' vs ')
     - Empty string handling
     - Trailing punctuation with small words
     - McName recursive calls
     - Split/join behavior with empty parts

3. **Iterate until 1.0**:
   - Fix in small batches
   - Re-run `harbor run -p . -a oracle` after each fix
   - Score must reach exactly 1.0

### Step 1-4: Documentation (Missing)
- [ ] Clone python-titlecase repo
- [ ] Create NOTES.md with:
  - License (MIT)
  - Git SHA and date
  - 8+ titlecase rules with examples
  - Edge cases that agents get wrong
- [ ] Verify Dockerfile copies python-titlecase correctly
- [ ] Verify gen.py generates deterministic test data

### Step 7: Validation
- [ ] Run nop agent (must score 0.0)
- [ ] Create and test cheat solution (must score < 0.2)

### Step 8: Submission
- [ ] Push to GitHub
- [ ] Add screenshots of oracle 1.0, nop 0.0, cheat < 0.2
- [ ] Document which rules agents got wrong

## Commands to Run

### Debug current failures:
```bash
harbor run -p ./titlecase-go -a oracle
# Check logs in jobs/<timestamp>/<trial>/verifier/test-stderr.txt for debug output
```

### After fixes, verify:
```bash
harbor run -p ./titlecase-go -a oracle  # Must show Mean: 1.000
harbor run -p ./titlecase-go -a nop     # Must show Mean: 0.000  
```

## Files Modified
- `tests/test.sh` - Added debug output, fixed reward.json writing
- `tests/gen.py` → `tests/gen.py.bak` - Renamed to avoid import errors
- `tests/debug_diff.py` - Added (new) for finding failing lines

## Next Steps
1. Run harbor with debug script to see which 13 test cases fail
2. Analyze patterns and fix Go code  
3. Iterate until oracle = 1.0
4. Complete remaining steps (nop, cheat, documentation)

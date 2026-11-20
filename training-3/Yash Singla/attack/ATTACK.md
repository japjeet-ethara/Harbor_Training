# Attack run results

**Target:** Piyush Khattar  
**Target commit:** `a95d51a1e503671dd28e2962e24858c33f88c5c0`  
Source: [`TARGET.txt`](TARGET.txt).

The grader uses a weighted mean: `build` weight 1, `no_python` weight 1, and `behaviour` weight 9 ([`target/tests/reward.toml:1-4`](target/tests/reward.toml#L1)). Each Harbor run below is a final run; failed debug runs are omitted.

## Cheat 1 — build-only blank-line stub

**Run:** `jobs/2026-11-19__23-56-57`  
**Reward:** `0.0909` — build `1`, no_python `0`, behaviour `0`.

The script created a minimal Go program that compiled and emitted a blank line per input line, without titlecasing. The build criterion only requires `go build ./...` to succeed ([`target/tests/build.py:7-18`](target/tests/build.py#L7)). The workspace still contained `.py` files, so the no_python criterion failed its recursive file check ([`target/tests/no_python.py:18-20`](target/tests/no_python.py#L18)). Blank output did not match the expected titlecase results, yielding behaviour `0`; behaviour is scored by the fraction of matching output lines ([`target/tests/behaviour.py:44-48`](target/tests/behaviour.py#L44)). Thus the reward is `1/11 = 0.0909` under the configured weights.

**One fix for Piyush:** make `build` and `no_python` prerequisites for behaviour credit instead of independently rewarded points, or award those points only after behaviour reaches a threshold. As currently configured, each independently adds weight to the weighted mean ([`target/tests/reward.toml:3-4`](target/tests/reward.toml#L3)); the behaviour score is computed separately as the matching-line fraction ([`target/tests/behaviour.py:44-48`](target/tests/behaviour.py#L44)).

## Cheat 2 — delete Python files plus blank-line stub

**Run:** `jobs/2026-11-20__00-06-12`  
**Reward:** `0.1818` — build `1`, no_python `1`, behaviour `0`.

The script deleted `.py` files and then wrote the same kind of buildable blank-line stub. That satisfies both the build check and the no_python criterion ([`target/tests/build.py:10-18`](target/tests/build.py#L10), [`target/tests/no_python.py:10-20`](target/tests/no_python.py#L10)). It still did not produce titlecased lines, so behaviour scored `0` ([`target/tests/behaviour.py:44-48`](target/tests/behaviour.py#L44)). The total is `(1 + 1 + 9×0)/11 = 0.1818` ([`target/tests/reward.toml:3-4`](target/tests/reward.toml#L3)).

**One fix for Piyush:** make `build` and `no_python` prerequisites for behaviour credit instead of independently rewarded points, or award those points only after behaviour reaches a threshold. This prevents a buildable stub that only passes those binary checks from collecting their current standalone weighted credit ([`target/tests/reward.toml:3-4`](target/tests/reward.toml#L3), [`target/tests/build.py:10-18`](target/tests/build.py#L10), [`target/tests/no_python.py:18-20`](target/tests/no_python.py#L18)).

## Cheat 3 — half port

**Run:** `jobs/2026-11-20__00-12-19`  
**Reward:** `0.3123` — build `1`, no_python `1`, behaviour `0.1595`.

The script deleted `.py` files and wrote a program that splits on whitespace, lowercases each word, uppercases its first rune, and rejoins with single spaces. It built and passed the no_python check. That approximation matched some hidden expected lines, but missed the special titlecase rules and preserved spacing requirements described by the task ([`target/instruction.md:5, 11, 21`](target/instruction.md#L5)). Behaviour is the fraction of expected output lines matching at the same index ([`target/tests/behaviour.py:44-48`](target/tests/behaviour.py#L44)); its `0.1595` partial score, combined with both binary criteria, gives `(1 + 1 + 9×0.1595)/11 = 0.3123` ([`target/tests/reward.toml:3-4`](target/tests/reward.toml#L3)).

**One fix for Piyush:** add more diverse hidden cases across the input features, and make the behavior criterion verify exact output length as well as byte-for-byte line and whitespace matching. The existing generator draws from a fixed set of word/token categories ([`target/tests/gen.py:45-69, 210-230`](target/tests/gen.py#L45)); the criterion compares expected lines by index but does not penalize extra trailing output ([`target/tests/behaviour.py:44-48`](target/tests/behaviour.py#L44)), while the task requires exact output bytes and whitespace handling ([`target/instruction.md:11, 21`](target/instruction.md#L11)). Gate build/no_python points on a behaviour threshold too: with behaviour at `0.1595`, withholding those two points leaves `(9×0.1595)/11 = 0.1305`, below `0.2`, using the current fixed weights ([`target/tests/reward.toml:3-4`](target/tests/reward.toml#L3)).

**Highest score: `0.3123`.**


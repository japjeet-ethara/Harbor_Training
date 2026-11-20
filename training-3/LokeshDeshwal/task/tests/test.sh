#!/bin/bash
set -eu

# ─── Harbor hardened test verifier for titlecase-go ───
#
# Hardening features:
#   1. Uses 100,000-input exam (inputs.txt / answers.txt)
#   2. Byte-exact streaming comparator (fixes tab-split awk gap)
#   3. Strict .py, .pyc, and __pycache__ cleanup verification
#   4. Gated scoring: build and no_python only awarded if behaviour >= 0.98
#   5. Non-linear threshold: partial ports (< 0.98) receive 0 behaviour reward
#
# Weights: build (1), no_python (1), behaviour (8) -> total 10

WORKSPACE="/workspace/repo"
TESTS_DIR="/tests"
LOGS_DIR="/logs/verifier"
mkdir -p "$LOGS_DIR"

# Resolve dataset paths
INPUTS_FILE="$TESTS_DIR/data/inputs.txt"
if [ ! -f "$INPUTS_FILE" ]; then
    INPUTS_FILE="$TESTS_DIR/data/hidden_inputs.txt"
fi

ANSWERS_FILE="$TESTS_DIR/data/answers.txt"
if [ ! -f "$ANSWERS_FILE" ]; then
    ANSWERS_FILE="$TESTS_DIR/data/hidden_expected.txt"
fi

# ─── Check 1: build ───
raw_build=0
if (cd "$WORKSPACE" && go build ./... >/dev/null 2>&1); then
    raw_build=1
fi

# ─── Check 2: no_python (including .pyc and __pycache__) ───
raw_nopy=0
py_count=$(find "$WORKSPACE" \( -name "*.py" -o -name "*.pyc" -o -name "__pycache__" \) 2>/dev/null | wc -l)
if [ "$py_count" -eq 0 ] && [ "$raw_build" -eq 1 ]; then
    raw_nopy=1
fi

# ─── Check 3: behaviour ───
raw_behaviour=0
if [ "$raw_build" -eq 1 ]; then
    binary=""
    for candidate in "$WORKSPACE/titlecase-go" "$WORKSPACE/titlecase" "$WORKSPACE/main"; do
        if [ -f "$candidate" ] && [ -x "$candidate" ]; then
            binary="$candidate"
            break
        fi
    done

    if [ -z "$binary" ]; then
        (cd "$WORKSPACE" && go build -o titlecase-go . >/dev/null 2>&1) || true
        if [ -f "$WORKSPACE/titlecase-go" ]; then
            chmod +x "$WORKSPACE/titlecase-go" 2>/dev/null || true
            binary="$WORKSPACE/titlecase-go"
        fi
    fi

    if [ -n "$binary" ] && [ -f "$binary" ]; then
        chmod +x "$binary" 2>/dev/null || true
        actual_file="/tmp/actual_output.txt"

        binary_exit=0
        "$binary" < "$INPUTS_FILE" > "$actual_file" 2>/dev/null || binary_exit=$?

        # Strict checks: binary must exit successfully (exit code 0) and generate output
        if [ "$binary_exit" -eq 0 ] && [ -s "$actual_file" ]; then
            python3 -c "
import itertools

with open('$actual_file', 'rb') as f_act, open('$ANSWERS_FILE', 'rb') as f_exp:
    m = 0
    act_count = 0
    exp_count = 0
    for a, e in itertools.zip_longest(f_act, f_exp, fillvalue=None):
        if e is not None:
            exp_count += 1
        if a is not None:
            act_count += 1
        if a is not None and e is not None and a.rstrip(b'\r\n') == e.rstrip(b'\r\n'):
            m += 1

    # Require full line count match; partial output earns 0
    if act_count != exp_count or exp_count == 0:
        score = 0.0
    else:
        score = m / exp_count

    with open('/tmp/behaviour.txt', 'w') as f_out:
        f_out.write(f'{score:.6f}')
"
            if [ -f "/tmp/behaviour.txt" ]; then
                raw_behaviour=$(cat /tmp/behaviour.txt)
            fi
        fi
        rm -f "$actual_file" /tmp/behaviour.txt
    fi
fi

# ─── Hardening Gates: close all cheat loopholes ───
# Cheats with < 0.98 accuracy get 0 behaviour and 0 structural points
behaviour_score=0
build_score=0
no_python_score=0

if [ "$(awk "BEGIN { print ($raw_behaviour >= 0.98) }")" -eq 1 ]; then
    behaviour_score=$raw_behaviour
    build_score=$raw_build
    no_python_score=$raw_nopy
fi

# ─── Final Composite Reward ───
# Total weight = 1 + 1 + 8 = 10
reward=$(awk "BEGIN { printf \"%.6f\", ($build_score * 1 + $no_python_score * 1 + $behaviour_score * 8) / 10 }")

# ─── Write reward.json ───
cat > "$LOGS_DIR/reward.json" << EOF
{
  "reward": $reward,
  "build": $build_score,
  "no_python": $no_python_score,
  "behaviour": $behaviour_score
}
EOF

echo "$reward" > "$LOGS_DIR/reward.txt"
echo "VERIFIER FINISHED: reward=$reward, build=$build_score, no_python=$no_python_score, behaviour=$behaviour_score"

"""Freeze answers from the original, keeping only inputs that give the same answer twice.

Usage: python answers.py <original_src_dir> <pool.txt> <out_dir>
Writes out_dir/inputs.txt, out_dir/answers.txt and out_dir/report.txt.
"""
import os
import subprocess
import sys

CHILD = ("import sys; sys.stdout.reconfigure(encoding='utf-8'); "
         "sys.path.insert(0, sys.argv[1]); import titlecase as m; "
         "lines = open(sys.argv[2], encoding='utf-8').read().split('\\n')[:-1]; "
         "print('\\x00'.join(m.titlecase(t) for t in lines), end=''); "
         "print('\\x01' + str(m.REGEX_AVAILABLE), end='')")


def run_once(src_dir, pool, hash_seed):
    env = {key: value for key, value in os.environ.items() if not key.upper().startswith("PYTHON")}
    env["PYTHONHASHSEED"] = str(hash_seed)
    out = subprocess.run([sys.executable, "-B", "-S", "-s", "-P", "-c", CHILD, src_dir, pool],
                         capture_output=True, text=True, encoding="utf-8",
                         env=env, check=True).stdout
    body, regex_flag = out.rsplit("\x01", 1)
    return body.split("\x00"), regex_flag


def main():
    src_dir, pool, out_dir = sys.argv[1], sys.argv[2], sys.argv[3]
    lines = open(pool, encoding="utf-8").read().split("\n")[:-1]
    first, regex_flag = run_once(src_dir, pool, 1)
    second, second_regex_flag = run_once(src_dir, pool, 2)
    if regex_flag != second_regex_flag or len(first) != len(lines) or len(second) != len(lines):
        raise ValueError("reference runs disagree on mode or number of answers")
    keep = [i for i in range(len(lines)) if first[i] == second[i]]
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "inputs.txt"), "w", encoding="utf-8", newline="\n") as f:
        f.writelines(lines[i] + "\n" for i in keep)
    with open(os.path.join(out_dir, "answers.txt"), "w", encoding="utf-8", newline="\n") as f:
        f.writelines(first[i] + "\n" for i in keep)
    report = [f"pool inputs        {len(lines)}",
              f"kept (stable)      {len(keep)}",
              f"dropped (unstable) {len(lines) - len(keep)}",
              f"regex module used  {regex_flag}"]
    with open(os.path.join(out_dir, "report.txt"), "w") as f:
        f.write("\n".join(report) + "\n")
    print("\n".join(report))


if __name__ == "__main__":
    main()

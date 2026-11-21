"""Keep only inputs whose reference output is stable across hash seeds.

Usage: python freeze_answers.py <original_src_dir> <pool.txt> <out_dir>
"""
import os
import subprocess
import sys

CHILD = (
    "import sys; sys.stdout.reconfigure(encoding='utf-8'); "
    "sys.path.insert(0, sys.argv[1]); import titlecase as m; "
    "lines = open(sys.argv[2], encoding='utf-8').read().split('\\n')[:-1]; "
    "print('\\x00'.join(m.titlecase(text) for text in lines), end=''); "
    "print('\\x01' + str(m.REGEX_AVAILABLE), end='')"
)


def run_once(source_dir, pool_path, hash_seed):
    env = dict(
        os.environ,
        PYTHONHASHSEED=str(hash_seed),
        PYTHONIOENCODING="utf-8",
    )
    try:
        result = subprocess.run(
            [sys.executable, "-I", "-c", CHILD, source_dir, pool_path],
            capture_output=True,
            text=True,
            encoding="utf-8",
            env=env,
            check=True,
        )
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(
            "Reference execution failed: "
            + (exc.stderr or exc.stdout or f"exit status {exc.returncode}")
        ) from exc
    body, regex_flag = result.stdout.rsplit("\x01", 1)
    return body.split("\x00"), regex_flag


def main():
    source_dir, pool_path, output_dir = sys.argv[1], sys.argv[2], sys.argv[3]
    with open(pool_path, encoding="utf-8") as pool_file:
        inputs = pool_file.read().split("\n")[:-1]
    first, regex_flag = run_once(source_dir, pool_path, 1)
    second, _ = run_once(source_dir, pool_path, 2)
    if len(first) != len(inputs) or len(second) != len(inputs):
        raise RuntimeError("Reference output count did not match pool input count.")
    keep = [index for index in range(len(inputs)) if first[index] == second[index]]

    os.makedirs(output_dir, exist_ok=True)
    with open(os.path.join(output_dir, "inputs.txt"), "w", encoding="utf-8", newline="\n") as output:
        output.writelines(inputs[index] + "\n" for index in keep)
    with open(os.path.join(output_dir, "answers.txt"), "w", encoding="utf-8", newline="\n") as output:
        output.writelines(first[index] + "\n" for index in keep)
    report = [
        f"pool inputs        {len(inputs)}",
        f"kept (stable)      {len(keep)}",
        f"dropped (unstable) {len(inputs) - len(keep)}",
        f"regex module used  {regex_flag}",
    ]
    with open(os.path.join(output_dir, "report.txt"), "w", encoding="utf-8", newline="\n") as output:
        output.write("\n".join(report) + "\n")
    print("\n".join(report))


if __name__ == "__main__":
    main()

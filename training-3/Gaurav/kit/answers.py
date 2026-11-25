"""Freeze answers from the original titlecase implementation twice."""
import os
import subprocess
import sys

CHILD = ("import base64,sys; sys.path.insert(0, sys.argv[1]); import titlecase as m; "
         "lines=open(sys.argv[2],encoding='utf-8').read().split('\\n')[:-1]; "
         "body='\\x00'.join(m.titlecase(t) for t in lines); "
         "print(base64.b64encode(body.encode('utf-8')).decode('ascii'),end=''); "
         "print('\\x01'+str(m.REGEX_AVAILABLE),end='')")


def run_once(src_dir, pool, hash_seed):
    env = dict(os.environ, PYTHONHASHSEED=str(hash_seed), PYTHONIOENCODING="utf-8")
    proc = subprocess.run(
        [sys.executable, "-I", "-c", CHILD, src_dir, pool],
        capture_output=True, text=True, encoding="utf-8", env=env,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"freeze run {hash_seed} failed with exit {proc.returncode}: "
            f"{proc.stderr[-4000:]}"
        )
    output = proc.stdout
    encoded, regex_flag = output.rsplit("\x01", 1)
    import base64
    body = base64.b64decode(encoded).decode("utf-8")
    return body.split("\x00"), regex_flag


def main():
    src_dir, pool, out_dir = sys.argv[1], sys.argv[2], sys.argv[3]
    lines = open(pool, encoding="utf-8").read().split("\n")[:-1]
    first, regex_flag = run_once(src_dir, pool, 1)
    second, _ = run_once(src_dir, pool, 2)
    keep = [i for i in range(len(lines)) if first[i] == second[i]]
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "inputs.txt"), "w", encoding="utf-8", newline="\n") as f:
        f.writelines(lines[i] + "\n" for i in keep)
    with open(os.path.join(out_dir, "answers.txt"), "w", encoding="utf-8", newline="\n") as f:
        f.writelines(first[i] + "\n" for i in keep)
    report = [
        f"pool inputs        {len(lines)}",
        f"kept (stable)      {len(keep)}",
        f"dropped (unstable) {len(lines) - len(keep)}",
        f"regex module used  {regex_flag}",
    ]
    with open(os.path.join(out_dir, "report.txt"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(report) + "\n")
    print("\n".join(report))


if __name__ == "__main__":
    main()

import os
import sys
import json
import subprocess

def is_elf_executable(path):
    if not os.path.isfile(path):
        return False
    try:
        with open(path, "rb") as f:
            magic = f.read(4)
            return magic == b"\x7fELF"
    except Exception:
        return False

def main():
    repo_dir = "/workspace/repo"
    data_dir = "/tests/data"
    logs_dir = "/logs/verifier"
    os.makedirs(logs_dir, exist_ok=True)

    build_score = 0.0
    no_python_score = 0.0
    behaviour_score = 0.0

    # 1. Build check
    print("Checking 'go build ./...' in", repo_dir)
    build_proc = subprocess.run(
        ["go", "build", "./..."],
        cwd=repo_dir,
        capture_output=True,
        text=True
    )
    if build_proc.returncode == 0:
        build_score = 1.0
        print("Build succeeded!")
    else:
        print("Build failed with exit code:", build_proc.returncode)
        print("stderr:", build_proc.stderr)
        print("stdout:", build_proc.stdout)

    # 2. No python check
    py_files = []
    if os.path.exists(repo_dir):
        for root, dirs, files in os.walk(repo_dir):
            for file in files:
                if file.endswith('.py'):
                    py_files.append(os.path.join(root, file))

    if build_score == 1.0 and len(py_files) == 0:
        no_python_score = 1.0
        print("No python files detected and build passed!")
    else:
        print(f"No-python check failed: {len(py_files)} .py files found or build failed.")
        if py_files:
            print("Found python files:", py_files[:5])

    # 3. Behaviour check
    if build_score == 1.0:
        # Check standard binary name first
        binary_path = None
        standard_path = os.path.join(repo_dir, "titlecase")
        if is_elf_executable(standard_path):
            binary_path = standard_path
        else:
            # Search for any ELF binary in repo_dir
            for item in os.listdir(repo_dir):
                candidate = os.path.join(repo_dir, item)
                if is_elf_executable(candidate):
                    binary_path = candidate
                    break

        if not binary_path:
            # Compile explicitly to /tmp/titlecase
            build_explicit = subprocess.run(
                ["go", "build", "-o", "/tmp/titlecase", "."],
                cwd=repo_dir,
                capture_output=True,
                text=True
            )
            if build_explicit.returncode == 0 and is_elf_executable("/tmp/titlecase"):
                binary_path = "/tmp/titlecase"

        if binary_path and os.path.exists(binary_path):
            print("Executing binary:", binary_path)
            hidden_inputs = os.path.join(data_dir, "hidden_inputs.txt")
            hidden_expected = os.path.join(data_dir, "hidden_expected.txt")

            with open(hidden_inputs, "r", encoding="utf-8") as f:
                inp_data = f.read()

            with open(hidden_expected, "r", encoding="utf-8") as f:
                expected_lines = f.read().splitlines()

            run_proc = subprocess.run(
                [binary_path],
                input=inp_data,
                cwd=repo_dir,
                capture_output=True,
                text=True,
                timeout=120
            )

            actual_lines = run_proc.stdout.splitlines()

            matches = 0
            total = len(expected_lines)
            for i in range(min(len(actual_lines), total)):
                if actual_lines[i] == expected_lines[i]:
                    matches += 1

            behaviour_score = matches / float(total) if total > 0 else 0.0
            print(f"Behaviour: {matches}/{total} matches ({behaviour_score * 100:.2f}%)")
        else:
            print("Could not locate or produce Go binary for behaviour evaluation.")

    # Weighted mean: build (1), no_python (1), behaviour (4)
    total_weight = 1.0 + 1.0 + 4.0
    final_reward = (1.0 * build_score + 1.0 * no_python_score + 4.0 * behaviour_score) / total_weight
    final_reward = round(final_reward, 4)

    rewards = {
        "build": build_score,
        "no_python": no_python_score,
        "behaviour": round(behaviour_score, 4),
        "reward": final_reward
    }

    reward_json_path = os.path.join(logs_dir, "reward.json")
    with open(reward_json_path, "w", encoding="utf-8") as f:
        json.dump(rewards, f, indent=2)

    reward_txt_path = os.path.join(logs_dir, "reward.txt")
    with open(reward_txt_path, "w", encoding="utf-8") as f:
        f.write(str(final_reward) + "\n")

    print(f"Grading completed. Reward: {final_reward}")
    print(json.dumps(rewards, indent=2))

if __name__ == "__main__":
    main()

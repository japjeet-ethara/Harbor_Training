import os
import random
import sys

# Add python-titlecase to path from environment folder
repo_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "environment", "python-titlecase"))
sys.path.insert(0, repo_path)

from titlecase import titlecase

WORDS = [
    "apple", "banana", "orange", "pear", "grape", "lemon", "peach",
    "the", "a", "an", "and", "but", "or", "for", "nor", "of", "at", "by", "to", "in", "on",
    "NASA", "FBI", "HTML", "CSS", "API", "JSON", "CLI", "OS",
    "http://example.com/test", "https://github.com",
    "well-known", "user-friendly", "up-to-date",
    "don't", "can't", "it's", "john's", "o'connor",
    "\"great\"", "'quoted'", "hello: world", "question? answer", "exclamation! mark"
]

def generate_sentence():
    length = random.randint(3, 8)
    chosen = [random.choice(WORDS) for _ in range(length)]
    sentence = " ".join(chosen)
    # Ensure no internal newline characters
    return sentence.replace("\n", " ").strip()

def main():
    random.seed(1)
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    os.makedirs(data_dir, exist_ok=True)

    inputs_file = os.path.join(data_dir, "inputs.txt")
    expected_file = os.path.join(data_dir, "expected.txt")
    hidden_inputs_file = os.path.join(data_dir, "hidden_inputs.txt")
    hidden_expected_file = os.path.join(data_dir, "hidden_expected.txt")

    print("Generating 2000 visible test titles...")
    with open(inputs_file, "w", encoding="utf-8") as f_in, open(expected_file, "w", encoding="utf-8") as f_exp:
        for _ in range(2000):
            line = generate_sentence()
            f_in.write(line + "\n")
            f_exp.write(titlecase(line) + "\n")

    print("Generating 2000 hidden test titles...")
    with open(hidden_inputs_file, "w", encoding="utf-8") as f_in, open(hidden_expected_file, "w", encoding="utf-8") as f_exp:
        for _ in range(2000):
            line = generate_sentence()
            f_in.write(line + "\n")
            f_exp.write(titlecase(line) + "\n")

    print("Done generating test sets.")

if __name__ == "__main__":
    main()
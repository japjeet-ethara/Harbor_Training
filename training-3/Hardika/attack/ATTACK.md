# Attack on Kushal Soni's task

- **Target:** `training-3/KushalSoni/task/` at commit `42e9bfe` (full SHA in `TARGET.txt`).
- **How every cheat was run:** on a local copy of the task with only `solution/solve.sh` replaced, using Harbor 0.26.0:
  `harbor run -p <copy> --env docker -a oracle`. Job folders are kept locally (not pushed).
- **Score formula** (`tests/reward.toml:4`): reward = (build + no_python + 4 × behaviour) / 6.

## Cheat 1 — Build trick

```
What it does:   Deletes the .py files and writes an empty Go program (func main() {}).
                It compiles, reads nothing and prints nothing.
Score:          reward 0.3333  (build 1, no_python 1, behaviour 0)
Job folder:     jobs/2026-11-23__12-07-58
Why it worked:  tests/reward.toml:4 gives build and no_python 2 of the 6 weight points.
                tests/build.py:38-41 and tests/no_python.py:30-36 pay them whenever the
                repo compiles, no matter what the program prints.
                (behaviour.py:50-54 correctly gave 0: that part is strong.)
How to fix:     Pay build and no_python only when behaviour is already high (for example
                behaviour >= 0.5), or make them pass/fail gates that set the whole reward
                to 0, instead of points that add up on their own.
```

# Rudransh — Day 4 Attack Results

This folder contains the Day 4 attack report and the unchanged copy of my practice task. I tested Aaditya Markande's `titlecase-go` Harbor task at commit `ee7e3dfbb6da17d4eafa86734973ec53e08206bc`.

## Harbor score

The target verifier computes the reward as:

```text
(build + no_python + 4 × behaviour) / 6
```

`behaviour` is the fraction of hidden inputs whose output matches the expected answer. The results below are from actual Harbor runs using the `oracle` agent.

| Attack | Build | No Python | Behaviour | Reward | Harbor job |
|---|---:|---:|---:|---:|---|
| Visible-answer lookup | 1 | 1 | 0.000000 | **0.333333** | `day4-cheat1-lookup-isolated` |
| Hidden-answer file read | 1 | 1 | 0.000000 | **0.333333** | `day4-cheat2-hidden-read-isolated` |
| Python reference relocation | 1 | 1 | 0.500000 | **0.666667** | `day4-cheat3-python-relocation-rerun` |

The Python relocation cheat earned partial behavior credit and the highest reward, **0.666667**. The lookup and hidden-answer probes earned build and no-Python points but matched none of the hidden outputs.

## Attack notes

- **Visible-answer lookup:** attempted to read the visible input and answer files, then used a simple capitalization fallback. It earned no behavior credit.
- **Hidden-answer read:** attempted to read and replay the hidden answer file at runtime. It earned no behavior credit.
- **Python relocation:** copied the Python reference outside `/workspace/repo`, removed `.py` files from the checked directory, and invoked the reference from a Go wrapper. This bypassed the filename scan and matched half of the hidden outputs.

The scoring gap is also visible in the first two results: passing the build and no-Python checks alone gives **0.333333** even with zero behavioral matches.

## Evidence

The copied Harbor reward files are in [`attack/results/`](attack/results/). The full attack discussion, limitations, and possible fixes are in [`attack/ATTACK.md`](attack/ATTACK.md). `TARGET.txt` records the exact target commit.

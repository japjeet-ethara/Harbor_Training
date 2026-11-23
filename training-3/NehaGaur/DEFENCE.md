# Day 6 Defence Report

**Author:** Neha Gaur  
**Task:** titlecase-go  
**Branch:** training-3

## 1. Strongest Cheat: Answer Peeking

The strongest original attack was Answer Peeking, which scored 1.000 before hardening. It built a Go program that attempted to read `/tests/data/hidden_expected.jsonl` directly and print the expected answers instead of implementing titlecase.

## 2. Defence Strategy

I applied two main protections:

- **Candidate privilege isolation:** The candidate program runs as the unprivileged `nobody` user (UID/GID 65534).
- **Answer-file protection:** The hidden expected-answer file is restricted with `chmod 0600`, preventing the unprivileged candidate process from reading it.

I also changed the reward calculation so structural checks cannot earn reward without correct behavior:

```python
reward = scores["behavior"] * (scores["build"] + scores["no_python"] + 4) / 6
```

## 3. Before/After Exam Comparison

| Participant | Before hardening | After hardening |
|---|---:|---:|
| Lokesh | 0 / 2,000 | 3,142 / 100,000 |
| Neha | 0 / 2,000 | 503 / 100,000 |
| Saurabh | 0 / 2,000 | 0 / 100,000 |

The after-hardening measurements use a 100,000-input exam pool.

## 4. Day 6 Verification Results

| Test | Reward | Exceptions |
|---|---:|---:|
| Oracle | 1.000 | 0 |
| NOP | 0.000 | 0 |
| Cheat 1: Answer Peeking | 0.000 | 0 |
| Cheat 2: Delete & Build | 0.000 | 0 |
| Cheat 3: Naive Capitalizer | 0.000 | 0 |

All three attacks scored below the required 0.2 threshold.

The corresponding Harbor result files are saved in `training-3/NehaGaur/proof/`.

## 5. What Surprised Me

The most surprising result was that Answer Peeking, which originally achieved a perfect reward of 1.000, dropped to 0.000 after the privilege and file-permission protections.

The two structural cheats also dropped to 0.000 because the reward now depends on behavioral correctness.

## 6. Conclusion

The hardened task preserves correct behavior for the oracle while rejecting the no-op baseline and all three tested cheats. The Day 6 verification results confirm Oracle 1.000, NOP 0.000, and all cheats below 0.2.

# Defence Report

## 1. Final verification results

The hardened task was evaluated against the correct implementation, a no-operation baseline, and three previously developed cheating submissions.

| Submission | Reward | Expected result | Status |
|---|---:|---:|---|
| Oracle | 1.00 | 1.00 | Passed |
| NOP | 0.00 | 0.00 | Passed |
| Cheat 1 | 0.05 | Below 0.20 | Passed |
| Cheat 2 | 0.05 | Below 0.20 | Passed |
| Cheat 3 | 0.05 | Below 0.20 | Passed |

All five results matched the required thresholds.

## 2. Security improvements

### Cheat 1: Accessing hidden test data

The original vulnerability allowed a submission to exploit access to test fixtures.

**Defence:** The verifier loads fixtures into memory and sends inputs to a static Go executable inside a fresh chroot. The process runs as an unprivileged user, and the jail contains only the executable. Expected answers remain in verifier memory and are never exposed to the submitted program.

**Result:** Reward reduced from 1.00 to 0.05.

### Cheat 2: Using an external Python implementation

The attack attempted to use Python or other external execution mechanisms instead of implementing the required solution.

**Defence:** The jail contains no Python interpreter. Workspace checks reject Python files, shebangs, ELF files, disallowed Go imports, and process-launch markers.

**Result:** Reward reduced from 1.00 to 0.05.

### Cheat 3: Exploiting build credit

The attack exploited the reward structure by obtaining credit without producing sufficiently correct output.

**Defence:** Behaviour now accounts for 90% of the reward. Workspace-check credit is awarded only when behavioural performance reaches at least 0.9. A buildable submission with no correct output receives only 5% build credit.

**Result:** Reward reduced from 0.3333 to 0.05.

## 3. Correctness verification

The final Oracle achieved a reward of 1.000 with zero exceptions.

Additionally, I compared three Go implementations against the same frozen reference suite of 100,000 inputs:

| Implementation | Incorrect answers |
|---|---:|
| My Oracle | 0 |
| Madhur Jain | 857 |
| Saurabh Baghel | 3,520 |

This comparison demonstrated that a successful build does not guarantee behavioural correctness. A large frozen test suite exposed subtle differences that smaller tests could miss.

## 4. Evidence

- Oracle reward: [proof/oracle/reward.json](proof/oracle/reward.json)
- NOP reward: [proof/nop/reward.json](proof/nop/reward.json)
- Cheat 1 reward: [proof/cheat1/reward.json](proof/cheat1/reward.json)
- Cheat 2 reward: [proof/cheat2/reward.json](proof/cheat2/reward.json)
- Cheat 3 reward: [proof/cheat3/reward.json](proof/cheat3/reward.json)
- Hardening report: [HARDEN.md](HARDEN.md)

## 5. Conclusion

The final evaluation demonstrates that the task rewards genuine behavioural correctness rather than merely successful compilation or access to hidden test data.

The verifier protects expected answers, restricts the execution environment, and makes behavioural correctness the primary source of reward.

The Oracle achieved full reward, the NOP received zero, and all three cheating submissions fell to 0.05. These results demonstrate that the implemented defences successfully addressed the tested attack strategies.
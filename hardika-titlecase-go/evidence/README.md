# Evidence

| Check | Observed result |
| --- | --- |
| Two generations of the four dataset files | Identical bytes and SHA-256 hashes. Each split has 2,000 unique records. Cross-split input and answer overlap were both zero. |
| Frozen-answer verification | Original Python and the Go executable each matched all 4,000 frozen records. |
| Independent differential stress | All 120,000 unique cases matched byte for byte. |
| Stream contract | Empty input, blank records, CRLF, missing final LF, embedded CR and a 560,001-byte input all passed. |
| Local grader on Windows | Oracle fixture 1.0, nop fixture 0.0 and visible replay fixture 0.16666666666666666. A Python-delete-only fixture scored 0.0. Replay with Python removed scored 0.3333333333333333. |
| Harbor static lint | Harbor 0.26.0 reported zero findings with all static rules selected. |
| Standalone Docker images | Both shipped Dockerfiles built and passed their smoke checks. Explicit network-disabled runs verified that the agent image contains its writable starter repo and that the candidate UID cannot read hidden answers in the verifier. |

The independent checks ran on Windows with the pinned Go and reference Python versions in [reproducibility.log](reproducibility.log). The complete frozen comparison is in [frozen-reference-release.log](frozen-reference-release.log). The [recorded commands](commands.md) describe the validation procedure.

## Harbor runtime results

| Run | Build | Python removal | Behavior | Recorded reward |
| --- | ---: | ---: | ---: | ---: |
| Oracle | 1.0 | 1.0 | 1.0 | **1.0** |
| Nop | 0.0 | 0.0 | 0.0 | **0.0** |
| Visible-answer replay | 1.0 | 0.0 | 0.0 | **0.1667** |

The final baseline run used Harbor 0.26.0 with the Docker backend, Docker Desktop 4.98.0 (engine 29.9.2), and Ubuntu on WSL 2. It used the shipped Linux/amd64 images and the task's default separate, offline agent and verifier policy. See [wsl-validation-final.log](wsl-validation-final.log), [wsl-isolation-check.log](wsl-isolation-check.log), and [final-reward-check.log](final-reward-check.log). The [Harbor jobs](harbor-wsl/titlecase-harbor.Xb0PNTj9/jobs/) preserve the raw verifier reward JSON, Reward Kit details, and job and trial metadata. Each final trial finished with zero exceptions.

The [three screenshots](reward-screenshots/) are headless Microsoft Edge captures of local HTML views populated from the unmodified final Harbor reward JSON. Each view displays the trial’s relative path and recorded component and aggregate values. The corresponding HTML files, capture code, browser version, and image hashes are included with the evidence.

## Earlier attempts

The managed Windows shell initially received access denied on Docker Desktop’s engine pipe. The scratch Alpine/QEMU VM built both images and exposed an oracle failure where the Linux Go build output collided with the upstream `titlecase/` directory. The final Go module uses `titlecase-port`. Reward Kit groups now expose the three requested component scores in `reward.json`. The earlier Linux build and trial logs remain in this directory and under `harbor-qemu/`.

After Docker Desktop became accessible, the first WSL attempt scored 1.0 on the oracle before Harbor lost its Windows-mounted working directory between jobs. The baseline script now runs from its scratch directory. The complete WSL rerun recorded all three scores above.

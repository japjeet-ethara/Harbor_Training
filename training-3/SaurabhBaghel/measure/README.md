# Exam and port measurements

## Exam construction

The expanded pool was generated with `kit/make_pool.py` using count `100000` and seed `1`. `kit/answers.py` was run twice against the task's pinned reference environment, where `regex==2024.11.6` is installed (`REGEX_AVAILABLE=True`). Both freezes retained 100,000 of 100,000 inputs with no unstable answers, and the input and answer files were byte-identical between freezes.

| Suite | Inputs | Answers | Records | SHA-256 |
| --- | --- | --- | ---: | --- |
| Old exam | [inputs.txt](./old-exam/inputs.txt) | [answers.txt](./old-exam/answers.txt) | 2,000 | input `FCACECF46C9355E355398C3EA18E6A86D1820F9DEC4D3743660308291B49C953`; answers `52C630D7091F7CDA10095931751126DECC6DCB3B44A0EBA47D787A783BF3D55F` |
| Expanded exam | [inputs.txt](./new-exam/inputs.txt) | [answers.txt](./new-exam/answers.txt) | 100,000 | input `779B81D3930A23B0F3AF5CF56EF19DE29DEA3CB632E6ACA1FCE2A5E20DA9606F`; answers `25EC52D967DA7098A6C9FC1B06897BF6BC586967B14ADC90657383148CF5AAE1` |

The expanded pair is also installed at `../task/tests/data/inputs.txt` and `../task/tests/data/answers.txt`. Freeze outputs and reports are retained under [new-exam/](./new-exam/).

## Port comparison

All six measurements used `kit/compare.py` with the original exam and the expanded exam. The detailed output, including representative mismatches, is in the linked reports.

| Port | Old exam | Expanded exam |
| --- | ---: | ---: |
| SaurabhBaghel | [0 / 2,000 wrong](./ports/SaurabhBaghel-old.txt) | [0 / 100,000 wrong](./ports/SaurabhBaghel-new.txt) |
| Gaurav | [54 / 2,000 wrong](./ports/Gaurav-old.txt) | [10,503 / 100,000 wrong](./ports/Gaurav-new.txt) |
| SakshiSingh | [60 / 2,000 wrong](./ports/SakshiSingh-old.txt) | [10,488 / 100,000 wrong](./ports/SakshiSingh-new.txt) |

`kit/make_pool.py` is the expanded-family version from the local training kit; `kit/answers.py` and `kit/compare.py` are the trainer-kit scripts. Their recorded mode is `regex`, as required by [instruction.md](../task/instruction.md).

The oracle and cheat verifier outputs are retained under [attacks/](./attacks/).

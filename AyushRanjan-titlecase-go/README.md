Titlecase in Go



Overview



This Harbor task ports the behavior of the original Python titlecase library to Go.



The implementation reads input text, applies title-case conversion rules, and writes the converted output while preserving the expected behavior of the reference implementation.



Implementation



Implemented in Go.



Uses a shell-based solution entry point.



Handles title-case rules, including small words and special capitalization cases.



Includes regression and behavior tests.



Verification



The task was successfully evaluated using Harbor.



Final Harbor Score: 1.000 / 1.000



Behavior: 1.000



Build: 1.000



No Python dependency: 1.000



Project Structure



instruction.md - Task instructions.



task.toml - Harbor task configuration.



environment/ - Reference Python project and environment setup.



solution/ - Go implementation.



tests/ - Verification scripts, criteria, and test data.



reward ss.png - Screenshot of the successful Harbor evaluation.



Harbor Evaluation


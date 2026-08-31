# AGENTS.md

## Scope
- This repository is for the fluorosis intelligent diagnosis paper scaffold.
- Current focus: `Stage4` only.

## Rules
- Keep changes minimal and scoped.
- Do not implement non-Stage4 logic unless explicitly requested.
- Preserve the structure and constraints from the project docx in `references/`.

## Verification
- Prefer small, direct checks after edits.

## Project Structure
- `src/`: core Stage4 code, including the Neo4j client, graph retrieval, and report generation modules.
- `tests/`: unit tests and minimal verification cases for `src/`.
- `configs/`: runtime configuration files for Stage4.
- `cli/`: demo scripts and command-line entry points for manual checks.
- `references/`: source materials and constraint references to check before editing.
- `versions/`: coding versions control.

## 其他
- 每次版本更改都需要经过全量的单元测试，并保证所有测试项目都通过；
- 版本迭代后，输出测试命令，我需要审查测试是否都通过，并且给我版本对应demo的示例命令；
- 每个版本迭代，代码都先不要提交，我需要审查代码；
- 提示词文档用.md文件进行保存；
- 注意中文内容的处理，避免出现中文乱码的情况发生；

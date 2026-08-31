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

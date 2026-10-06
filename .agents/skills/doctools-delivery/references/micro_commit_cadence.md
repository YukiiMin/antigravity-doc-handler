# Reference: Micro-Commit Cadence & Git Workflow Protocol

## 1. Core Principles
- **Deterministic & Compact**: Each commit encapsulates exactly one verified sub-step `X.Y.Z`. Never bundle multiple distinct sub-steps into a single commit.
- **Fail-Closed**: Never commit if any test fails or linter checks raise errors.
- **Strict Human Authority**: The Agent NEVER executes `git commit` or `git push` without explicit user confirmation.

## 2. Branch & Commit Message Conventions
- **Development Branches**:
  - `feat/phase-1-docx`: Dedicated to Phase 1 DOCX deliverables.
  - `feat/phase-2-xlsx`: Dedicated to Phase 2 XLSX deliverables.
  - `feat/phase-3-diagram`: Dedicated to Phase 3 DIAGRAM deliverables.
  - `chore/agent-context-architecture`: Dedicated to agent customization and context optimization.
- **Commit Message Structure**:
  ```
  <type>(<scope>): <concise description> [<Gate / Spec Ref>]
  ```
  Examples:
  - `feat(docx): implement SchemaHelper, TagOrderRegistry, and PackageIO [DOCX-D-06, ERR_DOCX_001]`
  - `feat(docx): implement TemplateLinter and JinjaNormalizer [DOCX-FR-01, FR-02, D-09]`
  - `chore(agent): optimize context rules to English core with bilingual triggers`

## 3. Step-by-Step Delivery Workflow
1. Complete source code for `X.Y.Z` (< 300 lines/file).
2. Author accompanying unit tests verifying behavioral contracts.
3. Execute the full test suite: `python -m unittest discover -s tests`.
4. Update `.agent_scratchpad.md` documenting completion.
5. Display summary report and propose exact `git commit` command for user approval.
6. Upon explicit user confirmation, execute commit and push to remote sub-repo `antigravity-doc-handler`.

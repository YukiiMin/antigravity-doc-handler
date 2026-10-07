# doctools — Document & Diagram Engineering Engine Quickref

> **Sub-repo Root Context**. Applies to the entire `tool/pdf_to_docx_converter`.
> Architecture: `README.md` | Master Plan: `ai_native_toolkit_modular_architecture_plan.md` | Task State: `.agent_scratchpad.md`

---

## 1. CHECKPOINT Recovery Protocol (MANDATORY)

When receiving a `{{ CHECKPOINT N }}` signal or when context is reset:
1. **Read this file** (`GEMINI.md`) — confirm core invariants and scope boundaries.
2. **Read `.agent_scratchpad.md`** — retrieve current goal, completed steps, and remaining TODOs.
3. Do not execute code actions immediately — confirm state first before responding to the user.

---

## 2. Module Map & Context Loading Architecture (Glob / Progressive)

The system operates via **Hierarchical Scope + Glob Rules + Progressive Skills**:

| Module | Source & Test Directories | Auto-Triggered Rule (Glob) | Domain Skill (.agents/skills/) |
|---|---|---|---|
| **DOCX** | `doctools/core/docx/`, `doctools/operations/docx/`, `tests/test_docx/` | `rule_docx_engine_standards.md` | `doc-handler` |
| **XLSX** | `doctools/core/xlsx/`, `doctools/operations/xlsx/`, `tests/test_xlsx/` | `rule_xlsx_engine_standards.md` | `excel-handler` |
| **DIAGRAM** | `doctools/core/diagram/`, `doctools/operations/diagram/`, `tests/test_diagram/` | `rule_diagram_engine_standards.md` | `mxgraph-diagram-engineering` |
| **QA / GATES** | `doctools/gates/`, `tests/conformance/` | `rule_quality_gate_and_verification.md`, `rule_enterprise_document_and_spreadsheet_qa.md` | `doctools-delivery` |
| **DELIVERY** | Entire repo during micro-commit `X.Y.Z` execution | `rule_git_workflow.md`, `rule_substep_cadence_and_context_refresh.md` | `doctools-delivery` |

*Note*: Detailed OpenXML invariants (`ERR_DOCX_*`), 14 Excel invariants (`E1–E14`), and 21 Draw.io invariants (`MX_INV_01–21`) are automatically loaded via **glob triggers** when touching relevant files; they are never bloated into root context.

---

## 3. Core Project Invariants

1. **Scope Boundary & Git Invariant**:
   - ONLY commit/push to the sub-repo (`antigravity-doc-handler`). NEVER touch the main SAP repo.
   - **STRICT PROHIBITION on unapproved commits**: Only execute `git commit` / `git push` upon explicit user consent (*"commit this"*, *"proceed with commit"*).
2. **Failure Discipline (Max 1 Fix Attempt)**:
   - Maximum 1 fix attempt per error. If it fails or introduces new errors: STOP immediately, explain the root cause, and await user feedback. Never guess blindly.
3. **File Size Limit & Code Formatting**:
   - All newly created code files MUST strictly adhere to **< 300 lines/file**.
   - NEVER truncate code blocks with placeholders like `// rest of code remains unchanged`.
4. **Dual-Run Preservation & Zero Python at Root**:
   - Source code must reside strictly in `doctools/`, `tests/`, and `legacy_engines/`. Never leave standalone Python scripts at the repository root.
5. **Task & Scratchpad Discipline**:
   - Maintain `.agent_scratchpad.md` at workspace root. Read at the start of each iteration and update before ending the response.

---
trigger: model_decision
description: Sub-step verification cadence, automated micro-commit cadence, and mandatory context refresh protocol before starting the next sub-step in Phase 1. Quy chuẩn nghiệm thu tiểu bước 1.x.x, tự động micro-commit, nạp lại context, nạp spec trước khi code, chống hallucination.
---

# Rule: Sub-Step Cadence, Automated Micro-Commit & Context Refresh Protocol

> **Scope**: Mandatory operational protocol executed at the completion of every sub-step (`X.Y.Z`) across `doctools` development.  
> **Goal**: Enforce verifiable quality gates, automate micro-commits under granted authority, and eliminate hallucination or context drift by refreshing exact specs before coding the next sub-step.

---

## 1. The 5-Gate Sub-Step Completion Protocol

Every time a sub-step (`X.Y.Z`) is implemented, the Agent MUST execute the following 5 gates sequentially:

```
[Implement Sub-step Logic & Tests]
                │
                ▼
  [Gate 1: 100% Test Suite Green] ──► Fails? ──► Max 1 Fix Attempt (Halt if unresolved)
                │
                ▼
  [Gate 2: Code Metrics Audit]    ──► Verify < 300 lines/file & no circular imports
                │
                ▼
  [Gate 3: Scratchpad Sync]       ──► Record completed progress, decisions & next goal
                │
                ▼
  [Gate 4: Automated Git Commit]  ──► git add ., git commit -m "...", git push origin <branch>
                │
                ▼
  [Gate 5: Context Refresh Gate]  ──► Re-read next sub-step spec from plan BEFORE coding
```

---

## 2. Gate 1: Test Suite Verification (`test_gate`)
- Run full regression suite: `python -m unittest discover -s tests`.
- Must achieve **100% PASS** (0 failures, 0 errors).
- Never proceed to commit if any test fails.

---

## 3. Gate 2: Code Metrics & Architecture Compliance
- Scan newly created or modified files: **MUST be strictly $< 300$ lines/file**.
- Adhere to single write-path rules (Schema Helper for Word OOXML, lxml for Excel cache).
- No direct circular dependencies between modules.

---

## 4. Gate 3: Scratchpad Synchronization
- Update `.agent_scratchpad.md` immediately with:
  - Check off completed sub-step item.
  - Document key architectural decisions made.
  - Set the next sub-step as the active immediate goal.

---

## 5. Gate 4: Automated Micro-Commit Execution
- Under the pre-approved autonomous authority for Phase 1:
  - Stage changes: `git add .`
  - Commit using Conventional Commits format with sub-step and spec codes:
    `git commit -m "<type>(<scope>): <concise description> [<Gate/Spec Code>]"`
  - Push branch to remote: `git push origin <branch>`.
  - Confirm clean working tree via `git status`.

---

## 6. Gate 5: Mandatory Context Refresh Gate (Anti-Hallucination)
- **STRICT PROHIBITION**: NEVER begin coding the next sub-step immediately based on conversational memory alone.
- Prior to touching or writing any file in the next sub-step:
  1. Open and view the exact section in `docs/update-spec/docx-engine-mcp-plan.md` and `ai_native_toolkit_modular_architecture_plan.md`.
  2. Confirm inputs, outputs, error codes (`E-DOCX-*`), and invariants required.
  3. Formulate the concrete implementation plan based on refreshed context.

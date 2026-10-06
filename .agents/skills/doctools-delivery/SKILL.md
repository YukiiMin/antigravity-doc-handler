---
name: doctools-delivery
description: Delivery protocol and verification cadence for doctools: Micro-Commit Cadence (X.Y.Z), Git workflow gates, diagnostics triage, and cross-module pipelines. Nghiệm thu mã nguồn, kỷ luật commit, quy trình phân phối, commit cho tôi, chẩn đoán lỗi, pipeline liên module.
---

# Skill: doctools-delivery

> **Purpose**: Standardize the development, verification, delivery, and acceptance protocol between solo developers and AI agents across the `doctools` suite.

---

## 1. When to Use
Activate this skill when:
- Starting or completing a phase or sub-step in the Master Plan (`X.Y.Z`).
- Running test suites, verifying quality gates, and packaging Git commits.
- Coordinating cross-module pipelines (e.g., XLSX $\rightarrow$ DOCX, DIAGRAM $\rightarrow$ DOCX).
- Triaging engine diagnostics, errors, and warnings.

---

## 2. Micro-Commit Cadence (`X.Y.Z`) & Git Gate

Core cadence for every development phase:
1. **Micro-Cadence Code Structure**:
   - `X`: Major phase (`1`: DOCX, `2`: XLSX, `3`: DIAGRAM).
   - `Y`: Feature priority tier (`1`: MVP, `2`: P1, `3`: P2).
   - `Z`: Verifiable sub-step (`0`, `1`, `2`...).
2. **Verifiable Gate Discipline**:
   - Each sub-step `X.Y.Z` requires independent unit tests.
   - Run the full test suite to confirm **100% PASS**.
   - The Agent halts, prints test pass evidence, and proposes a commit command.
   - **MANDATORY explicit user approval before executing `git commit` and `git push`**.
   - See [references/micro_commit_cadence.md](references/micro_commit_cadence.md).

---

## 3. Decision Tree: Triage & Delivery Flow

```
                      [Implement Sub-step X.Y.Z]
                                  │
                                  ▼
                     [Run Comprehensive Test Suite]
                                  │
           ┌──────────────────────┴──────────────────────┐
           ▼                                             ▼
     [Tests Failed]                               [100% Tests PASS]
           │                                             │
     [Max 1 Fix Attempt]                                 ▼
   Attempt single fix attempt                   [Propose Git Commit]
           │                                 Format: feat(scope): ... [Gate]
    ┌──────┴──────┐                                      │
    ▼             ▼                                      ▼
[Pass 100%]    [Still Fails]                    [Explicit User Approval]
    │             │                                      │
    │       HALT IMMEDIATELY!                            ▼
    │       Explain root cause,                 [Execute Commit & Push]
    │       await user guidance                          │
    │                                                    ▼
    └───────────────────────────────────────► [Advance to X.Y.(Z+1)]
```

---

## 4. Diagnostics Triage & Cross-Module References

- **Diagnostics Triage**: See [references/diagnostics_triage.md](references/diagnostics_triage.md) for categorizing `errors` vs `warnings` (`W-DEV-*` triggers `/grill-me`).
- **Cross-Module Pipelines**: See [references/cross_module_pipelines.md](references/cross_module_pipelines.md) for integrated pipelines combining DOCX, XLSX, and DIAGRAM.

---
trigger: model_decision
description: Git workflow and commit discipline for solo developers collaborating with AI agents in large modular projects. Quy chuẩn git, kỷ luật commit, micro-commit cadence X.Y.Z, commit cho tôi, đẩy code, push branch, cô lập sub-repo.
---

# Rule: Git Workflow & Commit Protocol (Solo Dev + AI Agent)

> **Scope**: Mandatory for the entire development lifecycle of the `doctools` suite (`tool/pdf_to_docx_converter`).  
> **Goal**: 100% prevention of lost operational context, zero git log pollution with broken code, and safeguarding a clean `main` branch.

---

## 1. Branching Model

The project operates under a hybrid branching architecture (Hybrid Phase Branching + Micro-Commit):

```
                        ┌──► [archive/legacy-v1 branch] (Preserves v1 baseline & learnings on GitHub)
                        │
[Current Baseline] ─────┤
                        └──► [feat/phase-0-foundation] ──► [feat/phase-1-docx] ──► [Merge to main]
                             (Contains micro-commits)                               (100% clean, production ready)
```

1. **`main` Branch (Production Baseline)**:
   - Must remain permanently Green, clean, and free of intermediate artifacts, temporary logs, or heavy test dumps.
   - Users cloning `main` receive strictly the clean modular toolkit (`doctools/`, `tests/`, `docs/`, `pyproject.toml`).
2. **`archive/legacy-v1` Branch (Museum Branch)**:
   - Preserves all legacy v1.0 monolithic scripts, benchmarks, and diagnostic utilities in `legacy_engines/`.
   - Pushed to remote (`git push origin archive/legacy-v1`) as an immutable historical reference.
3. **Phase Feature Branches (`feat/phase-X-...`)**:
   - Each major phase runs on a dedicated feature branch: `feat/phase-0-foundation`, `feat/phase-1-docx`, `feat/phase-2-xlsx`, `feat/phase-3-diagram`.
   - Work advances linearly through verifiable micro-commits (`X.Y.Z`).
   - Merge to `main` occurs strictly when the phase passes 100% of Quality Gates and Dual-Run parity tests.

---

## 2. Commit Cadence (Verifiable Sub-Step Gate Cadence)

NEVER commit blindly; NEVER batch an entire phase into a single massive commit:

1. **Commit Trigger**:
   - A commit is triggered **IMMEDIATELY** when a discrete module or sub-step is complete AND **its corresponding test suite passes 100%**.
   - *Example*: `file_store.py` complete + 100% passing `test_file_store.py` $\rightarrow$ triggers commit readiness.
2. **Authority Boundary**:
   - The AI Agent **MUST NEVER** execute `git commit` or `git push` without explicit user confirmation.
   - Upon completing a sub-step, the Agent:
     1. Halts and displays evidence of 100% passing tests.
     2. Proposes a standardized Conventional Commit message with scope and gate codes.
     3. Awaits explicit user approval (*"proceed with commit"*, *"commit this"*) before executing `git commit`.

---

## 3. Commit Message Standards

Must follow **Conventional Commits with Scope & Gate/TC Codes**:

```
<type>(<scope>): <concise description in English> [<Gate/TC Code>]
```

### Standard Types (`type`):
- `feat`: New feature or module (e.g., `feat(infra): implement FileStore with TTL [UG-01, DGM-TC-01]`).
- `fix`: Bug fix or gate violation remedy (e.g., `fix(xlsx): resolve formula AST shift offset [E-XLSX-SHIFT-FORMULA]`).
- `test`: Adding or updating test cases (e.g., `test(diagram): add orthogonal routing edge cases [DGM-TC-22]`).
- `refactor`: Code refactoring without changing behavior (e.g., `refactor(sandbox): split sandbox runner into 5 sub-modules`).
- `docs`: Documentation, plans, specs, or rules updates (e.g., `docs(plan): update Master Plan v6 and agent context`).
- `chore`: Tooling configuration, linting, gitignore, environment cleanup.

### Valid Scopes (`scope`):
`infra`, `contract`, `docx`, `xlsx`, `diagram`, `registry`, `tests`, `docs`, `rules`, `agent`.

---

## 4. Failure & Recovery Protocol

When an error or failure occurs during execution:
1. **Max 1 Fix Attempt**: The Agent is permitted at most 1 fix attempt per failure.
2. **Preserve Dirty State & Display Git Diff**:
   - If the first attempt fails or introduces new errors $\rightarrow$ **HALT IMMEDIATELY**.
   - **Retain uncommitted dirty state**; print a summarized `git diff` for joint human-agent analysis.
   - NEVER run `git restore .` or `git reset --hard` blindly behind the user's back.
   - The user decides whether to guide another fix or revert to the previous green commit.

---

## 5. Sub-Repo Isolation Boundary

- All Git commands (`add`, `commit`, `branch`, `push`) MUST strictly operate within the sub-repo:
  `d:\Minh\For_myself\ZSCORT_GSU26_SAP05\tool\pdf_to_docx_converter` (remote `antigravity-doc-handler`).
- **NEVER** touch or commit into the parent SAP repository (`ZSCORT_GSU26_SAP05`) unless given an explicit command.

# Reference: Ready-to-Use Templates & Boilerplates

> **Module**: `agent-context-architecture`  
> **Purpose**: Provide standardized copy-paste templates for Root GEMINI, Sub-directory GEMINI, Glob Rules, Model-Decision Rules, and Skill Packages.

---

## 1. Root `GEMINI.md` Boilerplate (For Workspace Root — Under 80 Lines)

```markdown
# [Project Name] — Core Architecture & Invariants Quickref

> **Role**: Project navigation map and core operational invariants for AI agents.
> **Rule**: This file is ALWAYS-ON. Keep concise without narrative fluff.

---

## 1. Project Module Map

| Module | Path | Role & Boundaries | Active Rule Trigger |
|---|---|---|---|
| **Core Service** | `src/core/` | Domain logic, core algorithms | `rule_core_standards.md` (`src/core/**`) |
| **API / Transport** | `src/api/` | Handlers, routing, HTTP contracts | `rule_api_standards.md` (`src/api/**`) |
| **Infra / Database** | `src/infra/` | DB connections, ORM, external adapters | `rule_infra_standards.md` (`src/infra/**`) |

---

## 2. Supreme Invariants

1. **Approved Dependencies**: Use only dependencies declared in `pyproject.toml` / `package.json`.
2. **Testing Gate**: Every feature requires accompanying unit tests; test coverage $\ge 80\%$.
3. **Data Safety**: Never mutate user data destructively without backups.
4. **File Size Limits**: Keep code files strictly $< 300$ lines; modularize on threshold breach.

---

## 3. Delegation to Specialized Skills

- Feature implementation and multi-step workflows: Inspect `.agents/skills/<skill-name>/SKILL.md`.
- Quality auditing and troubleshooting: Trigger validation rules under `.agents/rules/`.
```

---

## 2. Sub-Directory `GEMINI.md` Boilerplate (For Sub-Modules — Under 25 Lines)

```markdown
# [Sub-Module Name] Context & Local Invariants

> **Scope**: Applies strictly to `path/to/submodule/` and nested directories.

## Mandatory Local Invariants:
1. **Dependency Isolation**: This module MUST NEVER import upward from transport or CLI layers.
2. **Structured Errors**: Wrap errors into domain-specific exceptions (`ModuleError`).
3. **Pure Functions**: Core computation functions must remain deterministic and side-effect free.
```

---

## 3. Glob Rule Boilerplate (`trigger: glob`)

```markdown
---
trigger: glob
globs: src/core/**/*.py, tests/core/**/*.py
description: Core service architecture standards and typing invariants
---

# Rule: Core Service Architecture Standards

> **Scope**: Automatically activated when viewing or mutating files in `src/core/`.

## 1. Architectural Guardrails
- Use Pydantic v2 models for all schema validation.
- Avoid direct `os.environ` reads in core layers; inject configuration dependencies.
```

---

## 4. Model Decision Rule Boilerplate (`trigger: model_decision`)

```markdown
---
trigger: model_decision
description: Quality audit, data preservation, and regression troubleshooting standards. Soát lỗi chất lượng, kiểm định dữ liệu, phòng ngừa hồi quy.
---

# Rule: Quality Audit & Regression Prevention

> **Scope**: Loaded dynamically when tasks involve QA, failed tests, or code review.

## 1. Failure Protocol
- Maximum 1 fix attempt per error; halt and isolate root cause if unresolved.
- Never suppress linter warnings without explicit technical justification.
```

---

## 5. Standard Skill Package Structure (`.agents/skills/<name>/`)

### Directory Layout:
```
.agents/skills/<skill-name>/
├── SKILL.md                          # (Mandatory) Core instructions & decision tree
├── references/                       # (Optional) Lazy-loaded deep domain knowledge
│   └── deep_dive_topic.md
└── scripts/                          # (Optional) Deterministic executables
    └── automated_check.py
```

### `SKILL.md` Template:
```markdown
---
name: skill-name
description: Clear English description of the skill capability, followed by common Vietnamese trigger keywords. Mô tả năng lực và từ khóa kích hoạt.
---

# Skill: Skill Title

> **Purpose**: One-sentence operational summary of business value.

## 1. When to Use
- Scenario triggers and use cases...

## 2. Step-by-Step Core Workflow
1. Step 1: Pre-flight inspection...
2. Step 2: Core execution...
3. Step 3: Verification and delivery...

## 3. Companion References
- [references/deep_dive_topic.md](references/deep_dive_topic.md): Troubleshooting edge cases.
```

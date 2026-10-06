---
name: agent-context-architecture
description: Hierarchical context architecture and progressive disclosure system for AI agents (GEMINI.md, Rules, Skills, Specs, and Scripts). Kiến trúc phân tầng ngữ cảnh, tối ưu token budget, thiết kế rules và skills, chống context bloat, walk-up scoping.
---

# Skill: Agent Context Architecture (AI-Native System)

> **Goal**: Establish the optimal Hierarchical Context Architecture for Antigravity IDE, Cursor, and Claude, eliminating 100% of "Context Bloat" and "Lost in the Middle" degradation.

---

## 1. When to Use
Activate this skill when:
- Bootstrapping a new project requiring an AI Agent operating standard (`GEMINI.md`, `.agents/rules/`, `.agents/skills/`).
- Refactoring or optimizing an existing project suffering from context bloat or red warnings (exceeding 12,000 characters or 20,000 token active rule budget).
- Deciding whether a technical constraint belongs in **GEMINI.md**, a **Rule**, a **Skill**, or a **Spec**.
- Migrating legacy monolithic workflows into modular packaged skills.

---

## 2. The 5-Layer Context Model

Never treat all markdown files as generic "context files". Each component has a distinct role and activation lifecycle:

| Layer | Component | Activation Mechanism | Role & Budget |
|---|---|---|---|
| **Layer 1** | **GEMINI.md / AGENTS.md** | **Always On** (within folder scope) | Project navigation map, module directory, supreme invariants. **Root $\le 100$ lines**, **Module $\le 40$ lines**. No frontmatter. |
| **Layer 2** | **.agents/rules/*.md** | **glob**, **model_decision**, **always_on**, **manual** | Mandatory invariants, coding standards, architectural guardrails. Maximum 20,000 token active budget; max 12,000 chars/file. |
| **Layer 3** | **.agents/skills/** | **Progressive Disclosure** (discovered via name + description) | Modular capabilities: `SKILL.md` (instructions) + `references/` (deep knowledge) + `scripts/` (executables). |
| **Layer 4** | **SPEC / DOCS** | **On-Demand / Reference** | Technical specifications, data contracts, mapping dictionaries. Read strictly when requested by an Agent or Skill. |
| **Layer 5** | **SCRIPTS** | **Black-Box Execution** | Heavy deterministic algorithms (pixel measurement, layout calculation, format diffing). Executed via tools, never guessed by LLM. |

---

## 3. Decision Tree: Where Does Information Belong?

Use this decision tree when introducing new instructions into the system:

```
                            [I want to add information to the system]
                                                │
                 ┌──────────────────────────────┴──────────────────────────────┐
                 ▼                                                             ▼
     [Mandatory Constraint / Invariant]                           [Operational Capability / Workflow]
                 │                                                             │
     ┌───────────┴───────────┐                                                 ▼
     ▼                       ▼                                        [Create New Skill Package]
[Global / Cross-Cutting] [Module-Specific]                             .agents/skills/<name>/SKILL.md
     │                       │                                                 │
     ▼                       ▼                                   ┌─────────────┴─────────────┐
[GEMINI.md (Root)]      [Choose Rule Trigger]                    ▼                           ▼
(Concise ≤ 100 lines)        │                            [Core Workflow]             [Deep Reference]
                             ├─ Touches specific files? ──► trigger: glob             references/<topic>.md
                             ├─ Depends on task context? ──► trigger: model_decision
                             └─ Only on user request?   ──► trigger: manual
```

---

## 4. Rule Frontmatter Standards

In Antigravity IDE, rule frontmatter MUST adhere to the following schemas:

```yaml
# 1. Deterministic file path activation:
---
trigger: glob
globs: doctools/**/docx/**, tests/test_docx/**, **/*.docx
description: Concise bilingual summary for fallback semantic matching
---

# 2. Semantic evaluation activation (requires rich description):
---
trigger: model_decision
description: Enterprise Document & Spreadsheet QA standards... Kiểm toán chất lượng tài liệu văn phòng...
---

# 3. Always active (use sparingly, consumes persistent budget):
---
trigger: always_on
---

# 4. Manual user invocation only (@rule-name):
---
trigger: manual
---
```

---

## 5. Companion Reference Guides

- [references/5_layer_context_model.md](references/5_layer_context_model.md): Deep-dive analysis of the 5 layers and Walk-Up Scoping mechanisms.
- [references/activation_modes_and_triggers.md](references/activation_modes_and_triggers.md): Detailed comparison of the 4 rule triggers and preventing empty `globs:` warnings.
- [references/progressive_disclosure_and_budgets.md](references/progressive_disclosure_and_budgets.md): Managing the 20,000 token active budget and lazy-loading techniques.
- [references/templates_and_boilerplates.md](references/templates_and_boilerplates.md): Ready-to-use boilerplate templates (Root GEMINI, Module GEMINI, Glob Rule, Model-decision Rule, SKILL package).

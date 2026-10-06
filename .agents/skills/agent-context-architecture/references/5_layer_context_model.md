# Reference: 5-Layer Context Model & Walk-Up Scoping

> **Module**: `agent-context-architecture`  
> **Purpose**: In-depth analysis of the 5-layer context model and directory walk-up scoping mechanisms in AI-native engineering.

---

## 1. Nature of the 5 Context Layers

In large software projects, packing all documentation into prompt context at once causes **Context Saturation** and **Lost in the Middle** performance degradation (agents forget instructions buried in lengthy documents). The 5-layer context model partitions information into distinct operational tiers:

```
┌─────────────────────────────────────────────────────────────────┐
│ Layer 1: GEMINI.md / AGENTS.md (Root & Sub-directories)        │
│          - Always-on within folder scope                        │
│          - Module navigation, routing, supreme invariants       │
├─────────────────────────────────────────────────────────────────┤
│ Layer 2: .agents/rules/*.md                                    │
│          - Coding standards, guardrails, invariant constraints  │
│          - Triggered via Glob, Model Decision, Always-on        │
├─────────────────────────────────────────────────────────────────┤
│ Layer 3: .agents/skills/<skill-name>/                          │
│          - Operational capabilities and workflows               │
│          - Triggered on-demand via Progressive Disclosure       │
├─────────────────────────────────────────────────────────────────┤
│ Layer 4: Specs & Architecture Documents (docs/, specs/)        │
│          - Technical source of truth                            │
│          - Inspected on-demand when an agent requires deep specs│
├─────────────────────────────────────────────────────────────────┤
│ Layer 5: Deterministic Execution Scripts (scripts/, tools/)    │
│          - Heavy algorithms, CLI tools, format diffs, metrics   │
│          - Black-box execution, eliminating LLM guesswork       │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Walk-Up Scoping Mechanism of GEMINI.md / AGENTS.md

### 2.1. Operational Principle
When an agent operates on a file located at:
`/project/services/order_service/handlers/create_order.py`

The system automatically scans upward (walk-up) from the active directory to the workspace root:
1. `services/order_service/handlers/GEMINI.md` (if present)
2. `services/order_service/GEMINI.md` (if present)
3. `services/GEMINI.md` (if present)
4. `/project/GEMINI.md` (Root project context)

### 2.2. Inheritance and Isolation Rules
- **Root `GEMINI.md`**: Contains project-wide maps, module catalogs, and supreme invariants governing the whole repository. Target size: $\le 80$ lines (maximum 100 lines).
- **Sub-directory `GEMINI.md`**: Contains strictly local invariants and boundaries belonging to that specific package/module. Target size: $\le 20$–$30$ lines.
- **No Duplication**: Sub-directories never repeat rules defined at root. Root never descends into internal implementation minutiae of a sub-module.

---

## 3. Boundary Between Rules and Skills

A common pitfall is writing rules as procedural tutorials or turning skills into negative invariant lists:

| Criterion | Rules (`.agents/rules/`) | Skills (`.agents/skills/`) |
|---|---|---|
| **Purpose** | Protective guardrails, coding standards, invariants | Execution workflows, problem-solving methodologies |
| **Core Question** | *"What MUST I obey? What is STRICTLY FORBIDDEN?"* | *"HOW do I accomplish this complex task?"* |
| **Nature** | Mandatory, passive guardrails | Active, procedural capabilities |
| **Loading Trigger**| Automatic via file paths (Glob) or semantic intent (Model) | Reads `SKILL.md` when user intent matches description |
| **Budget** | Counts against the 20,000 token active rule budget | Isolated; loaded progressively on-demand |

---

## 4. Specs vs Scripts: Offloading LLM Cognitive Load

- **Specs (Layer 4)**: Define API schemas, database layouts, and logical component diagrams. The agent references (`view_file`) only the targeted section, avoiding reading 50-page specs in bulk.
- **Scripts (Layer 5)**: The agent determines high-level business logic; deterministic host scripts handle geometry calculations, coordinate measurements, and regression passes. Never force the LLM to guess coordinates in its head.

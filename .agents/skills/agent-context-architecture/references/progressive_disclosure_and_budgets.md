# Reference: Progressive Disclosure, Budgets & Workflow Deprecation

> **Module**: `agent-context-architecture`  
> **Purpose**: Guide to managing token budgets, applying progressive disclosure to lazy-load knowledge on demand, and deprecating legacy monolithic workflows in favor of modular skills.

---

## 1. Context Budgets & Hard Limits

When engineering AI rules and agent customizations, adhere strictly to three hard physical limits:

| Metric | Threshold | Impact of Exceeding Threshold |
|---|---|---|
| **Active Rules Budget** | **20,000 tokens** | When combined active rules exceed this limit, the system alerts in red or truncates context, causing prompt dilution and rule violations. |
| **Individual Rule File Size** | **12,000 characters** (~2,500 words) | IDE displays a red `XXXX/12000` counter. Overloaded files degrade local instruction following. |
| **GEMINI.md File Size** | **$\le 100$ lines** (Root) / **$\le 40$ lines** (Sub) | GEMINI.md injects into the prompt on every turn; excessive length dilutes user intent from Turn 1. |

---

## 2. The Progressive Disclosure Pattern

To provide hundreds of pages of technical domain expertise without breaching the 20,000 token active budget, apply **Progressive Disclosure**:

```
[Level 0: Skill Metadata - ~50 tokens]
  Agent scans skill catalog: name + description across all skills
            │
            ▼ (When relevant task intent is detected)
[Level 1: SKILL.md - ~500–1,000 tokens]
  Agent reads core workflows, summary tables, operational checklists
            │
            ▼ (When specialized troubleshooting is required)
[Level 2: references/<topic>.md - ~500 tokens per file]
  Agent selectively reads the specific reference matching the active issue
            │
            ▼ (When heavy calculations are needed)
[Level 3: scripts/ - 0 context tokens]
  Agent invokes deterministic scripts via CLI or MCP tools
```

### 2.1. Advantages Over Monolithic Documents
- Never loads entire rule encyclopedias simultaneously.
- Targeted inspection (`view_file` directed by precise pointers).
- Cuts token consumption and response latency by up to 80%.

---

## 3. Deprecation of Legacy Workflows

### 3.1. Official Google Antigravity Deprecation Notice
> **Official Notice**: The legacy **Workflows** subsystem (`.agents/workflows/` and `WORKFLOW.md`) is officially **deprecated** and will be sunset completely on **November 1, 2026**. All multi-step procedures must be restructured into modular **Skills**.

### 3.2. Why Workflows Were Deprecated
1. **Monolithic Bloat**: Legacy workflows crammed all steps into massive multi-hundred-line files, violating token budgets.
2. **Lack of Semantic Discovery**: Agents could not selectively inspect subsections based on task intent.
3. **Absence of Bundled Executables**: Workflows were purely passive text, lacking dedicated `scripts/` and isolated `references/`.

### 3.3. Migration Matrix

| Legacy Workflow (Removed) | Modern Standard Skill |
|---|---|
| `.agents/workflows/workflow_docx.md` | `.agents/skills/docx-handler/SKILL.md` |
| `.agents/workflows/workflow_xlsx.md` | `.agents/skills/excel-handler/SKILL.md` |
| `.agents/workflows/workflow_diagram.md` | `.agents/skills/mxgraph-diagram-engineering/SKILL.md` |
| `.agents/workflows/WORKFLOW.md` (Root) | `.agents/skills/doctools-delivery/SKILL.md` + `references/` |

---

## 4. Context Health Score Formula

Before concluding a phase or delivering an engineering milestone, calculate:

$$\text{Health Score} = \frac{\text{Tokens of Always-On Rules} + \text{Tokens of GEMINI.md}}{\text{20,000 Token Active Budget}} \times 100\%$$

- **Excellent**: $< 15\%$ (Baseline context under 3,000 tokens, reserving $\ge 85\%$ for inference and task state).
- **Warning**: $15\% - 30\%$. Migrate rules from `always_on` to `glob` or `model_decision`.
- **Critical**: $> 30\%$. Refactor immediately under the progressive disclosure model.

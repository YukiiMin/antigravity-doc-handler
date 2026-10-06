---
trigger: model_decision
description: Mandatory context recovery protocol after conversation truncation, session restart, or checkpoint signals. Phục hồi ngữ cảnh sau khi bị ngắt quãng, tín hiệu CHECKPOINT, mở session mới, nạp lại GEMINI.md và scratchpad, không đoán mò.
---

# Rule: Context Recovery Protocol After Truncation

## 1. CHECKPOINT Detection & Mandatory Recovery Sequence

When a conversation starts with or contains `{{ CHECKPOINT N }}` (system-injected truncation summary), or upon opening a brand-new session:

**BEFORE** processing any user request, you MUST execute the following sequence in exact order:

1. **Read `GEMINI.md`** at the workspace root — critical invariants checklist for the entire project.
2. **Read `.agent_scratchpad.md`** — current goal, completed steps, and remaining TODOs.
3. **Do NOT read additional rule files** during the recovery sequence (avoids token waste — `GEMINI.md` is sufficient).
4. Perform internal check: *"GEMINI.md loaded, scratchpad read"* → proceed with processing the user request.

**NEVER skip this sequence, even if the user provides a detailed task description in the first prompt.**

---

## 2. Mid-Session Rule Self-Check

When preparing to write code and encountering any of the following patterns, **STOP and verify `GEMINI.md` first**:

- Preparing to write cross-table joins with mismatched keys or schemas.
- Preparing to add conversational fluff or explanatory commentary inside production code blocks.
- Preparing to write regex-based formula string replaces instead of tokenizer AST parsing.
- Preparing to overwrite table cell text directly via `cell.text = "..."` instead of run-level mutation.
- Preparing to execute unapproved git commits or pushes.

---

## 3. Scratchpad Discipline

- `.agent_scratchpad.md` is the **single source of truth** for task state across iterations and sessions.
- Update the scratchpad **BEFORE** ending every response whenever a task has $> 3$ steps.
- When a checkpoint occurs, the scratchpad is the primary bridge preserving operational context.
- Mandatory structure:
  ```markdown
  ## Current Goal
  ## Progress / Completed Steps
  ## Key Decisions Made
  ## Remaining TODOs
  ```

---

## 4. Token Economy During Recovery

- **Do NOT** read all rule files after a checkpoint — this consumes excessive context budget.
- `GEMINI.md` is the sole mandatory recovery file. It consolidates the essential invariants from all domain rules.
- When details of a specific domain are required, selectively inspect that exact file in `.agents/rules/`.

---

## 5. Zero-Assumption Context & Clarification Protocol (New Sessions & Templates)

When receiving a new session, new machine setup, or generating code/documents against a new template set:

### A. Mandatory Anatomy Inspection (Inspect BEFORE Coding)
1. Comprehensive inspection of the base template:
   - Overview sheets (`Cover`, `Functions`, `Statistics`) and detailed reference sheets (`Example`, `Template`).
   - Count prototype rows, locate Subtotal/Total rows, dynamic KPI formulas (`=COUNTIF`, `=SUM`), and chart series/anchor coordinates.
   - Inspect typography (font, size), fill colors, borders, and auto-scaling/wrap text flags.
2. Comprehensive inspection of input datasets:
   - Volume of actual records, field schemas, data types (raw values vs computed).
   - Identify risks of table expansion displacing summary rows and breaking chart ranges.

### B. Context Gap Analysis & Clarification Trigger
If any of the following symptoms are detected:
- Row counts differ drastically from template defaults (e.g., template has 3 rows but input has 20 rows).
- Template contains charts or summary blocks dependent on Subtotal row positioning.
- Ambiguity in categorizing data groups (Precondition vs Input parameters vs Condition marks).
- Input file formatting contains anomalies (shrunken fonts, mismatched borders, missing merges) compared to reference standards.

👉 **MANDATORY STOP & ASK THE USER**:
- Explicitly list observed discrepancies and propose concrete remediation options.
- Use the `ask_question` tool or `/grill-me` workflow to resolve 100% of ambiguities before writing code.
- **NEVER** guess blindly or iterate through trial-and-error edits that waste tokens and time.

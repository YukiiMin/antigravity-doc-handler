# Rule: How to Write Rules & Skills (Meta-Rule for `/learn`)

> **Scope**: Applies every time `/learn` is invoked or a new rule/skill file is being authored.
> This rule governs the quality and generality of all rules and skills in this repository.

---

## Core Principle: Generalize the Mechanism, Never Memorize the Output

A learning is **only valuable** if it prevents an entire *class* of mistakes — not just a single instance.
Rules that hardcode a one-time observed value ("learned" from a specific file) are *learning vẹt* (rote memorization) and must be rejected.

---

## 1. Validity Criteria — When Is a Rule Valid to Write?

A rule **MUST satisfy at least one** of the following conditions:

| Condition | Description |
|---|---|
| **Generality ≥ 3** | The principle is applicable in 3 or more distinct situations across different files, projects, or domains. |
| **Critical Prevention** | User explicitly requests the rule be recorded to prevent one specific catastrophic mistake from ever recurring. Even if domain-specific, treat it as a protected invariant for that domain. |

A rule is **INVALID** (learning vẹt) if:
- It hardcodes a concrete observed value (a color hex, font name, pixel size, row number) from one specific file.
- The "rule" is really a description of what was done in one session — not a transferable principle.
- It cannot be applied by an AI that has never seen the original file, user, or session.

---

## 2. How to Write a Good Rule (Checklist)

### ✅ Ask "Why?" not "What?"
The rule must capture the **reasoning principle**, not the **observed outcome**.

| Bad (learning vẹt) | Good (transferable principle) |
|---|---|
| `Font for 'O' marks is Tahoma 12pt Bold` | `Extract mark cell font from the reference Example/Template sheet; never hardcode` |
| `fill = #000080` | `fill = extracted from ws_example[ref_cell].fill — the template's own value` |
| `Statistics C12 = ='Function 1'!A7` | `Summary cells MUST be live cross-sheet formulas; never hardcode aggregate numbers` |

### ✅ Replace concrete values with the derivation method
```
# Bad:
MARK_FONT = Font(name='Tahoma', size=12, bold=True)

# Good:
ref_cell = ws_reference["F15"]   # first 'O' mark cell in Example/Template sheet
MARK_FONT = copy(ref_cell.font)  # derived from the workbook itself, not guessed
```

### ✅ Triggerable in isolation
The rule must be actionable by an AI that has **never seen the original file**.
Test this by asking: "If I read only this rule with no other context, will I produce the correct behavior?"

### ✅ Abstract over projects and files
Never mention specific file names, sheet names, or cell addresses as the rule's anchor.
Use abstract concepts: "the reference sheet", "the first populated equivalent cell", "the template's established region".

---

## 3. The "One-Time Exception" Pattern

When user explicitly says **"record this specific case to never repeat it"**:

Write the rule with two parallel entries:

```markdown
[SPECIFIC CASE — <file/project/scenario>]:
  <Concrete description of what must never happen again>

[GENERAL PRINCIPLE]:
  <Abstract version applicable across any similar situation>
```

**Example:**
```markdown
[SPECIFIC CASE — Report5_Unit Test template]:
  Row 9 test case header style MUST be extracted from the
  existing Function 1 Row 9 cells — not recreated from a hardcoded font spec.

[GENERAL PRINCIPLE]:
  Before writing any style to a cell that already has a non-default style in the
  template, read that cell's current style first and preserve or extend it.
```

---

## 4. How to Write a Good Skill (Checklist)

### ✅ A skill = reusable workflow, NOT a rule
- Skills describe **how to execute a multi-step process** (commands, patterns, decision trees).
- Rules describe **what is forbidden or required** (invariants, constraints).

### ✅ Skills must reference rules, not duplicate them
```markdown
# In a skill:
> See `rule_excel_template_preservation_and_ux.md` for format extraction invariants.
# Do NOT re-paste the rule content — it will drift out of sync.
```

### ✅ Skills must contain runnable, testable artifacts
Every skill must include at minimum:
- A concrete CLI command or Python code pattern that works today.
- A success/failure signal the AI can observe.

---

## 5. `/learn` Session Workflow (Mandatory Steps)

1. **Identify the mistake class** — not just what broke, but *why* it would break again.
2. **Determine scope** — is this universal (≥3 scenarios) or critical-prevention (user-requested specific case)?
3. **Draft** the rule in `learning_proposal.md` artifact using the above checklist.
4. **Set `RequestFeedback = true`** — never modify rule/skill files before user approval.
5. **Execute** only after explicit approval (or auto-approval via review policy).
6. **Sync** to both repos if the rule applies to the tool sub-repository as well.

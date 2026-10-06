# Reference: Activation Modes, Triggers & Frontmatter Parsing

> **Module**: `agent-context-architecture`  
> **Purpose**: Standardize the 4 rule activation modes in Antigravity IDE, decode the internal parser mechanics, and prevent empty glob pattern UI warnings (`0/250`).

---

## 1. The 4 Rule Activation Modes

In Antigravity IDE, each rule file under `.agents/rules/*.md` can be configured with one of 4 activation triggers:

| Activation Mode | `trigger:` Property | Required Companion Field | When to Use | Token Cost |
|---|---|---|---|---|
| **Glob** | `glob` | `globs: <pattern>` | Rule applies strictly to specific files/directories (e.g., `*.docx`, `doctools/core/**`) | Highly optimal (Only loaded when touching matching files) |
| **Model Decision** | `model_decision` | `description: <text>` | Rule depends on task semantics (e.g., QA, Git, Delivery, Meta-learning) | Very efficient (Model evaluates relevance via description) |
| **Always-On** | `always_on` | *(none)* | Supreme invariants critical across every single turn and iteration | Highest cost (Occupies tokens in every prompt) |
| **Manual** | `manual` | *(none)* | Loaded strictly when user explicitly types `@rule_name` in chat | Zero automatic token cost |

---

## 2. Antigravity IDE Internal Parser Mechanics

The rule editor extension in Antigravity IDE (`extension.js`) parses frontmatter line-by-line rather than using a full YAML engine:

```javascript
// Frontmatter parser extraction from extension.js
const lines = rawText.split('\n');
let trigger = 'always_on';
let globParam = '';
let modelDecisionParam = '';

for (const line of lines) {
  if (line.startsWith('trigger:')) {
    trigger = line.replace('trigger:', '').trim();
  } else if (line.startsWith('globs:')) {
    globParam = line.replace('globs:', '').trim();
  } else if (line.startsWith('description:')) {
    modelDecisionParam = line.replace('description:', '').trim();
  }
}
```

### 2.1. Root Cause Analysis of "Glob Pattern 0/250"
When an author writes frontmatter missing the `globs:` field:
```yaml
---
trigger: glob
---
```
Because `globs:` is omitted, `globParam` defaults to empty string `''`. In the Custom Editor Webview UI:
- Dropdown **Activation Mode** shows `Glob`.
- Textbox **Glob Pattern** displays empty: `Enter glob pattern... 0/250`.
- **Consequence**: The rule is **NEVER triggered** because no file paths match an empty pattern!

---

## 3. Standard Syntax for Each Trigger Mode

### 3.1. Glob Mode Configuration
```yaml
---
trigger: glob
globs: doctools/**/docx/**, tests/test_docx/**, **/*.docx
description: Concise bilingual summary for fallback semantic matching
---
```
> **Note**: Separate patterns with commas `,`. Use `**` for recursive directory matching.

### 3.2. Model Decision Mode Configuration
```yaml
---
trigger: model_decision
description: Technical summary in English followed by Vietnamese semantic keywords
---
```
> **Note**: The `description` field MUST contain both concise English technical concepts and common Vietnamese domain keywords so the LLM triggers reliably across both languages.

### 3.3. Always-On Mode Configuration
```yaml
---
trigger: always_on
---
```
> **Guideline**: Reserve `always_on` strictly for emergency safety invariants or context recovery protocols. Never exceed 2 `always_on` rules in a repository.

### 3.4. Manual Mode Configuration
```yaml
---
trigger: manual
---
```

---

## 4. Pre-Flight Rule Checklist

- [ ] File has valid opening `---` and closing `---` frontmatter markers.
- [ ] If `trigger: glob` $\rightarrow$ contains `globs:` with valid patterns, never empty.
- [ ] If `trigger: model_decision` $\rightarrow$ contains `description:` with bilingual keywords.
- [ ] Total rule file size does not exceed 12,000 characters (IDE warning threshold).
- [ ] Webview UI verifies without empty `0/250` glob warnings.

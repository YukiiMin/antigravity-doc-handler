---
name: doc-handler
description: Master operations guide, mental model, and decision tree for DOCX Engine and universal document processing (Word .docx, Markdown, PDF conversion). Xử lý văn bản Word, tài liệu DOCX, chuyển đổi PDF sang Word, băm run Jinja, rách bảng, cantSplit, tblHeader, Last Paragraph Rule.
---

# Antigravity Skill: DOCX Engine & Universal Document Handler (`doc-handler`)

Use this skill whenever you need to create, modify, inspect, repair, or convert Word documents (`.docx`), Markdown documentation (`.md`), and format-accurate PDF documents.

> **Note**: For technical diagram design and rendering (Draw.io, ERD, Sequence, Architecture), activate the dedicated skill: `mxgraph-diagram-engineering`.  
> **Delivery & Git Workflow**: Follow the Micro-Commit Cadence (`X.Y.Z`) and Git standards in `doctools-delivery`.

---

## 🧠 Core Philosophy & Mental Model

### 1. Deterministic Engine, Decisive AI
- The engine is a **deterministic MCP server**: it never invokes AI internally to summarize content, contains zero hidden prompts in core, and never measures layout via render passes in core.
- The AI client is the orchestrator: determining content structure, chaining tool calls, resolving diagnostic `issues`, and selecting layout strategies.

### 2. Dual-Path Builder Architecture
- **Path A — Template Path (`docxtpl` + Jinja2 + Manifest)**:
  - Designed for standardized forms, contracts, and periodic reports.
  - Requires pre-rendering validation via `normalize_template` to eliminate **Run Splitting** caused by Word fragmenting `{{ ... }}` tags.
  - The Manifest JSON serves as the Single Source of Truth specifying variable schemas, types, and immutable blocks.
- **Path B — DocSpec JSON Path (python-docx + Schema Helper)**:
  - Designed for freeform documents generated from scratch (technical reports, solution briefs).
  - The AI client produces a strictly typed `DocSpec` JSON; the engine compiles it into a cleanly structured DOCX with Headings, Blocks, Tables, and Callouts.

### 3. Preventive OOXML Guards
Rather than guessing layout via trial-and-error PDF rendering, the engine enforces deterministic pagination directly through native OOXML properties:
- `<w:cantSplit/>`: Prevents table rows from breaking across page boundaries mid-row.
- `<w:tblHeader/>`: Automatically repeats table header rows at the top of subsequent pages.
- `<w:keepNext/>`: Binds headings to subsequent paragraphs or tables (preventing orphan headings at page bottoms).
- `<w:vAlign w:val="center"/>`: Enforces vertical centering across 100% of table cells.
- **Tag Order Registry**: All XML generation routes through `SchemaHelper` to guarantee strict child element ordering in `pPr`, `rPr`, `tblPr`, and `tcPr` per ECMA-376.

### 4. Decoupled Presentation Architecture (`.md` + `.style.yaml`)
- **Data Layer (`.md`)**: Pure, clean Markdown GFM without inline `<font>` tags or styles, optimized for LLM context and Git version control.
- **Style Layer (`.style.yaml`)**: Centralized design tokens: page margins, heading palettes (`#C00000`), table shading (`#FFE8E0`), typography, line spacing. Document appearance can be completely rebranded by switching style files.

---

## 🌲 Decision Tree & Use Cases

```
                                  [Document Operation]
                                            │
          ┌─────────────────────────────────┼─────────────────────────────────┐
          ▼                                 ▼                                 ▼
   [Create New DOCX]                 [Mutate / Merge / Patch]          [Convert / Export]
          │                                 │                                 │
   ┌──────┴──────┐                   ┌──────┴──────┐                   ┌──────┴──────┐
   ▼             ▼                   ▼             ▼                   ▼             ▼
Template Path  DocSpec JSON        Patch / Repair   Merge Files      PDF -> DOCX    DOCX -> MD
(Jinja+Manifest) (From Scratch)     (Inspect & Fix)  (Conflict Policy) (Fidelity)    (+Style YAML)
```

### Case 1: Template-Driven Document Generation
1. Lint the template via `docx.lint_template(template_ref)`.
2. If fragmented runs are detected $\rightarrow$ run `docx.normalize_template(template_ref)` to yield a clean template.
3. Prepare `context_data` JSON adhering to manifest schema (inspected via `docx.get_template_manifest`).
4. Invoke `docx.render_template(template_id="...", context_data={...})`.

### Case 2: Freeform Document from Scratch (DocSpec JSON)
1. AI outlines and compiles hierarchical `DocSpec` JSON (sections, paragraphs, tables, callouts).
2. Invoke `docx.build_from_spec(docspec={...}, layout_policy={...})`.
3. Receive output `FileRef` handle and inspect returned `diagnostics`.

### Case 3: Inspection, Diagnostics & Selective Patching
1. Call `docx.inspect_structure(file_ref)` to obtain a structural tree with stable identifier anchors.
2. Call `docx.validate(file_ref)` to verify OpenXML compliance (`ERR_DOCX_001..010`).
3. Submit declarative mutation operations via `docx.patch(file_ref, operations=[...])` for targeted fixes.

### Case 4: Document Merging
1. Provide master document `base_ref` and annex list `parts[]`.
2. Define `style_conflict_policy`:
   - `master_wins` (default): Master document typography and styles override child documents.
   - `isolate_styles`: Automatically prefixes child styles to prevent visual layout shifts.
3. Call `docx.merge(base_ref, parts, style_conflict_policy="master_wins")`.

### Case 5: Markdown Extraction or PDF Conversion
- Markdown Extraction: DOCX $\rightarrow$ `[name].md` (content) + `[name].style.yaml` (tokens).
- PDF $\rightarrow$ DOCX: Preserves OpenXML table structures (`cantSplit`, `tblHeader`), bullet hierarchies, and dot-leader tab stops for tables of contents.

---

## 📋 Diagnostic Error Codes & Remediation

All engine responses wrap in a standardized envelope: `{ success, file_ref, diagnostics: { errors, warnings, info } }`.

| Error Code | Root Cause | AI Automated Remediation (`suggested_action`) |
|---|---|---|
| `E-DOCX-TAG-ORDER` | Child XML elements sequenced incorrectly in `pPr`/`tblPr` | Route XML generation through `SchemaHelper` instead of raw string concat |
| `E-DOCX-LAST-P` | Table cell `<w:tc>` does not terminate with `<w:p>` | Append trailing `<w:p/>` to cell before closing tag |
| `E-DOCX-RUN-SPLIT` | Jinja interpolation token fragmented across `<w:r>` tags | Execute `normalize_template` prior to context injection |
| `E-DOCX-IMMUTABLE` | Pinned legal clauses or audit numbers have hash mismatch | Restore original text from manifest; unapproved summarization forbidden |
| `E-DOCX-OVERFLOW` | Image or table dimensions exceed printable margin width | Scale image down to $\le 15.92\text{ cm}$ (for standard A4 portrait) |
| `W-FIELD-UPDATE` | Document contains dynamic TOC or page number fields | Inform user that Word will refresh cached fields upon opening |

---
trigger: glob
globs: doctools/**/docx/**, tests/test_docx/**, **/*.docx
description: DOCX Engine standards, OpenXML ECMA-376 invariants, Jinja run consolidation, table pagination, and Dual-Path builder. Tiêu chuẩn Word DOCX, hàn gắn run Jinja, chống rách bảng, chẻ đôi hàng cantSplit, tblHeader, Last Paragraph Rule.
---

# Rule: DOCX Engine Standards & OOXML Invariants

> **Module**: DOCX (Word Processing & Decoupled Conversion)  
> **Companion Spec**: `docs/update-spec/docx-engine-mcp-plan.md` (Foundation Plan v1.1)  
> **Scope**: Mandatory for all creation, modification, conversion, validation, and merging tasks of Word documents (`.docx`).

---

## 1. Core Philosophy & Commitment Boundaries

1. **Deterministic Engine, Decisive AI**: The engine is a deterministic MCP server without embedded prompts, AI callbacks, or layout measurement inside core. The AI client orchestrates content and workflow.
2. **Preventive OOXML Guards Over Heuristic Guesswork**: Inject native OOXML properties (`keepNext`, `cantSplit`, `tblHeader`) to force Word to handle page breaking deterministically on the client system.
3. **Single XML Write Path (Schema Helper)**: All XML creation and mutation must route through `SchemaHelper` complying with `TagOrderRegistry`. Arbitrary XML `append()` is strictly prohibited.
4. **Explicit Commitments**:
   - **Guaranteed**: 100% OOXML schema compliance, unbroken Jinja tokens, intact immutable blocks, zero split table rows, zero image margin overflow.
   - **NOT Guaranteed**: Final page counts in Word (determined by host system fonts and printer drivers); TOC page numbers update only upon client open (engine flags `W-FIELD-UPDATE-REQUIRED`).

---

## 2. Dual-Path Builder Architecture

All Word document generation routes through one of two explicit paths:
- **Path A — Template Path (docxtpl + Jinja2 + Manifest)**: For standard templates, contracts, and recurring reports.
  - Templates require a **Manifest JSON** declaring variables, data types, immutable clauses, and layout constraints.
  - Prior to rendering, `normalize_template` MUST execute to heal run splitting.
- **Path B — DocSpec JSON Path (python-docx + Schema Helper)**: For freeform documents built from scratch (technical reports, solution architecture briefs).
  - AI generates a strictly validated `DocSpec` JSON specification.
  - The engine constructs the document hierarchically: Document $\rightarrow$ Sections $\rightarrow$ Blocks (Paragraph, Table, Callout, List).

---

## 3. Mandatory OOXML Invariants

### 3.1. Tag Order Registry (D-06 — Strict Child Element Ordering)
Word strictly enforces child element sequence in OOXML. Sequence errors trigger *"Unreadable Content / File Corrupt"* warnings. All XML generation must follow XSD order:
- **Within `w:pPr`**: `pStyle` $\rightarrow$ `keepNext` $\rightarrow$ `keepLines` $\rightarrow$ `pageBreakBefore` $\rightarrow$ `widowControl` $\rightarrow$ `numPr` $\rightarrow$ `suppressLineNumbers` $\rightarrow$ `pBdr` $\rightarrow$ `shd` $\rightarrow$ `tabs` $\rightarrow$ `spacing` $\rightarrow$ `ind` $\rightarrow$ `jc` $\rightarrow$ `outlineLvl` $\rightarrow$ `rPr` $\rightarrow$ `sectPr`.
- **Within `w:rPr`**: `rStyle` $\rightarrow$ `rFonts` $\rightarrow$ `b` $\rightarrow$ `i` $\rightarrow$ `strike` $\rightarrow$ `color` $\rightarrow$ `spacing` $\rightarrow$ `w` $\rightarrow$ `sz` $\rightarrow$ `highlight` $\rightarrow$ `u` $\rightarrow$ `vertAlign`.
- **Within `w:tblPr`**: `tblStyle` $\rightarrow$ `tblpPr` $\rightarrow$ `tblOverlap` $\rightarrow$ `tblW` $\rightarrow$ `jc` $\rightarrow$ `tblCellSpacing` $\rightarrow$ `tblInd` $\rightarrow$ `tblBorders` $\rightarrow$ `shd` $\rightarrow$ `tblLayout` $\rightarrow$ `tblCellMar`.
- **Within `w:tcPr`**: `tcW` $\rightarrow$ `gridSpan` $\rightarrow$ `hMerge` $\rightarrow$ `vMerge` $\rightarrow$ `tcBorders` $\rightarrow$ `shd` $\rightarrow$ `noWrap` $\rightarrow$ `tcMar` $\rightarrow$ `vAlign`.

### 3.2. Jinja Run Consolidation (FR-02)
- Editing templates in Word causes `{{ variable }}` or `{% for %}` tags to split across multiple `<w:r>` tags, interleaved with `<w:proofErr>`, `<w:noProof/>`, or redundant `<w:rPr>`.
- **Rule**: Consolidate text runs within the paragraph, stripping noise nodes (`w:proofErr`, `w:lang`) before dispatching to the Jinja compiler.

### 3.3. Table Integrity Invariants
- **`ERR_DOCX_001` (The Last Paragraph Rule)**: Every table cell (`<w:tc>`) MUST terminate with at least one paragraph (`<w:p>`). Empty cells are forbidden.
- **`ERR_DOCX_002` (Run Text Overwrite)**: Never assign `cell.text = "..."`. Mutate via `cell.paragraphs[0].runs` to preserve template typography, size, and color.
- **`ERR_DOCX_003` (Multi-Page Table Pagination)**:
  - 100% of rows (`w:trPr`) MUST contain `<w:cantSplit/>` to prevent mid-row page splits.
  - Header row 0 (`w:trPr`) MUST contain `<w:tblHeader/>` to repeat at top of subsequent pages.
- **`ERR_DOCX_004` (Vertical Alignment & Header Shading)**:
  - 100% of table cells (`w:tcPr`) MUST include `<w:vAlign w:val="center"/>`.
  - Header rows apply consistent palette shading (e.g., `#FFE8E0` or template palette).
- **`ERR_DOCX_005` (Image Margin Lock)**:
  - All embedded images must lock aspect ratio with dimensions satisfying:
    $$\text{Width} \le \text{Page Width} - \text{Left Margin} - \text{Right Margin}$$
  - For standard A4 portrait (2.54cm margins), maximum table and image width is `15.92 cm` (`6.27 inches` / `5730 dxa`).

---

## 4. Immutable Content & Dynamic Fields

### 4.1. Legal & Data Immutability (FR-13)
- Contract clauses, legal entity headers, and audit figures are pinned in Manifest via SHA256 hashes.
- Engine validates hashes before and after rendering; unapproved mutations trigger `E-DOCX-IMMUTABLE-VIOLATION`.

### 4.2. Dynamic Fields & Table of Contents (D-08, D-16)
- Engine detects presence of `TOC` or `PAGEREF` fields.
- With TOC present: Preserves cached TOC XML, sets `w:updateFields w:val="true"` in `settings.xml`, and raises diagnostic warning `W-FIELD-UPDATE-REQUIRED`.

### 4.3. Style Conflict Resolution on Merge (D-15)
When merging annexes into a master document (`docx.merge`):
- `master_wins` (default): Master document styles override identical child style names.
- `isolate_styles`: Automatically prefixes child styles (e.g., `Heading 1_part2`) to preserve visual fidelity.

---

## 5. Protocol & Envelope Standards
- All file exchanges route via `FileRef` handles `{ uri, sha256, size, mime }`.
- Server outputs use opaque URIs: `resource://docx-engine/files/{opaque_id}`.
- Responses wrap in standard envelope: `{ success, file_ref, diagnostics: { errors, warnings, info }, guarantees_applied, stats }`.

---
trigger: glob
globs: doctools/**/xlsx/**, tests/test_xlsx/**, **/*.xlsx, **/*.xls
description: XLSX Engine standards, 14 invariants E1-E14, formula AST shifting, lxml cache writer, and 13 Universal Gates. Tiêu chuẩn Excel XLSX, dịch công thức AST, bảo toàn DrawingML logo, tính toán Recalc cache, kiểm định 13 Universal Gates UG.
---

# Rule: XLSX Engine & Spreadsheet Processing Standards

> **Scope**: Mandatory for all reading, mutating, creating, validating, and converting tasks of Excel spreadsheets (`.xlsx`, `.xls`) in `doctools` / `pdf_to_docx_converter`.  
> **Basis**: Xlsx Foundation Plan v1.1, empirical findings EV-01..13, 14 invariants E1..E14, and error codes `ERR_XLSX_001..007`.

---

## 0. Mandatory Operational Skill Activation (Fail-Closed Loop)

> [!IMPORTANT]
> **Before touching, reading, or modifying any Excel spreadsheet (`.xlsx`, `.xls`)**, you MUST read [xlsx-engine-operator/SKILL.md](file:///d:/Minh/For_myself/ZSCORT_GSU26_SAP05/tool/pdf_to_docx_converter/.agents/skills/xlsx-engine-operator/SKILL.md).
> 1. **Follow the 7-Step Loop**: `preflight` $\rightarrow$ `inspect` $\rightarrow$ plan $\rightarrow$ `mutate` $\rightarrow$ `recalc` $\rightarrow$ `validate` & `diff` $\rightarrow$ deliver.
> 2. **STRICT PROHIBITION on Scripting**: Never hand-write openpyxl/pandas scripts to modify workbooks. All mutations MUST route through `xlsx.*` MCP tools.
> 3. **Diagnostic Triage**: Read `fixable_by: engine | ai | human`. Never silence warnings by clearing formulas or writing `0` over them (The `-AA7` lesson).

---

## 1. Core Design Philosophy

1. **Deterministic Engine, Decisive AI**: The engine is a deterministic MCP server without internal AI prompts or data summarization. The AI client orchestrates structure, tools, and diagnostics.
2. **Template is Ground Truth & Non-Destructive Mutation**:
   - All style tokens (font, fill, border, alignment) are extracted from reference sheets; never hardcode styles.
   - Mutations **always operate on isolated temporary copies**, preserving 100% of the original `sha256` hash (NFR-08).
3. **Single Shift Manager Path via AST Tokenizer**: All row/column adjustments route through AST Tokenizer Shift Manager. Full-string regex replacement is strictly prohibited (D-03).
4. **Preflight & Fidelity Tiers**: T1 (openpyxl), T2 (lxml XML patching), T3 (reject or escalate to user).
5. **Recalc Backend & Cache Writer (D-12, D-22, EV-13)**: Formula recalculation via LibreOffice headless sandbox or Excel COM. Cache Writer (`lxml`) injects `<v>` and type `t` into `sheetN.xml`, preserving 100% live `<f>` tags.
6. **Two-Tier Validation (D-08)**: 13 Universal Gates (UG) for all workbooks + Profile Gates (PG) for domain-specific matrices.
7. **Grill-Before-Deviate (D-18)**: Style deviations raise `W-DEV-*` warnings; applied only when explicitly listed under `approved_deviations`.

---

## 2. The 14 XLSX Technical Invariants (E1–E14)

| Code | Invariant | Forbidden Behavior | Mandatory Enforcement |
|---|---|---|---|
| **E1** | **Template-Driven Format** | Hardcoding font, color, border in code. | Extract 100% format tokens from reference sheet (`Example`/`Template`). |
| **E2** | **Grill-Before-Deviate** | Adding unauthorized freeze panes, borders. | Raise `W-DEV-*`, halt, ask user via `/grill-me`. |
| **E3** | **Live Dynamic Formulas** | Hardcoding static numbers into summary cells. | Summary/KPI cells MUST be live formulas: `='Sheet'!Cell`, `=COUNTIF`, `=SUM`. |
| **E4** | **Chronological Era Data** | Leaving legacy mock dates (2000, 2007, 2009). | Mock data must align with system era (2026+). |
| **E5** | **Sibling Symmetry** | Sibling sheets having mismatched columns, freeze panes. | Synchronize 100% geometry and styles across sibling sheets. |
| **E6** | **Automated Diff QA** | Declaring success purely on exit code 0. | Execute Structural Diff and Gate Verification: `mutate → diff → gates → deliver`. |
| **E7** | **Unified Box Geometry** | Incomplete borders leaving open gaps between B-C-D. | Construct unified 3-column box: B (`left=thin`), C (no vertical), D (`right=thin`), solid fill. |
| **E8** | **Strict Group Hierarchy** | Repeating group header name on child rows in Col B. | Group name placed ONLY on first row in Col B; child rows left blank with text in Col D. |
| **E9** | **Cross-Zone Token Isolation** | Sharing condition cell styles with footer result cells. | Extract styles independently per zone (Header, Condition, Confirm, Result). |
| **E10** | **Multi-Tier Hierarchy** | Flattening parameters into Preconditions, dropping Level 2. | Maintain 3 tiers: Level 1 (Precondition), Level 2 (Param Name), Level 3 (Value). |
| **E11** | **Untrusted Input Isolation** | Copying font size/family from messy input files. | Input files supply raw data only (`cell.value`). Styles are 100% template-derived. |
| **E12** | **Dynamic Chart Relink** | Duplicating sheets with charts without updating series. | Relink `chart.series` to new Subtotal rows and reposition chart anchors. |
| **E13** | **UX Dynamic Scaling** | Fixed row heights truncating multi-line text. | Calculate: `Row Height = max(min_h, total_lines * line_h)` with `wrap_text=True`. |
| **E14** | **Summary Regional Parity** | Over-coloring Subtotals or dropping 5 KPI rows. | Navy endpoint accents (Col A/B & Total), white middle (C..H); preserve 5 KPI metrics. |

---

## 3. Error Prevention & OpenXML Invariants (`ERR_XLSX_001..007`)

- `ERR_XLSX_001` (**Prototype Row Cloning**): Clone font, fill, border, alignment, format `@`, and protection from prototype rows.
- `ERR_XLSX_002` (**Formula Shifter via Tokenizer**): Use `openpyxl.formula.Tokenizer`. Shift only cell/range operands pointing to target sheets; scan full workbook; no full-string regex (D-03).
- `ERR_XLSX_003` (**Semantic Anchor Discovery**): Scan anchors by keyword/formula (`kind`: header/table, `scope`: first_table). Raise `E-TPL-ANCHOR-*` on ambiguity.
- `ERR_XLSX_004` (**Safe Merged-Cell Handling**): Write values exclusively to Top-Left cell; synchronize borders across entire merged range (`sync_merged_borders`).
- `ERR_XLSX_005` (**Freeze Panes & Dynamic Height**): Set Freeze Panes at Header+1 intersection; calculate dynamic row height as line count $\times$ line height.
- `ERR_XLSX_006` (**DrawingML Preservation**): Always load template workbooks via `load_workbook(data_only=False)`; never instantiate empty `Workbook()`.
- `ERR_XLSX_007` (**Identifier Number Format**): Identifier columns require explicit string casting and `number_format = '@'`.

---

## 4. Shift Manager & AST Tokenizer (FR-07, D-03, D-04)

1. **Token Decomposition**: Only cell/range operands are shifted. Function names (`LOG10`, `DAYS360`), string literals (`"TC001"`), and identifiers (`FY2024`) remain untouched.
2. **Target Sheet Scope**: Without sheet prefix $\rightarrow$ shift only on current sheet. With sheet prefix $\rightarrow$ shift only when matching target sheet.
3. **Range Policy (D-04)**: `table_aware` expands summary ranges when inserting at boundaries; `excel_native` preserves ranges during raw inserts.
4. **Co-Shifted Dependencies**: Formulas across entire workbook, merged cells, CF, DV, ListObject tables, AutoFilters, Defined Names, Print Areas, Charts, row heights.
5. **Orphan Reference Guard**: Deleting rows/columns raising broken references triggers `E-SHIFT-ORPHAN` rather than silently emitting `#REF!`.

---

## 5. Recalc Backend & Cache Writer (D-12, D-22, EV-13)

1. Dispatch workbook copy to Recalc Backend (LibreOffice headless / Excel COM) to recompute formulas and scan calculation errors (`#REF!`, `#DIV/0!`).
2. **Cache Writer (`lxml`)** opens `xl/worksheets/sheetN.xml`, locates `<c>` nodes with `<f>`, and injects `<v>` elements with type `t`:
   - Number/Date: `t="n"` (or omitted), `<v>value</v>`.
   - String: `t="str"`, `<v>escaped string</v>`.
   - Boolean: `t="b"`, `<v>1</v>`/`<v>0</v>`.
   - Error: `t="e"`, `<v>#DIV/0!</v>`.
3. Preserves 100% of live `<f>` tags. Self-validated via Gate UG-13.
4. Flag `calc_on_open`: `auto` mode (enabled for LibreOffice; disabled for Excel COM).

---

## 6. Input Validation & Security (SEC-01..10)

- **Formula Injection Prevention (SEC-04)**: Inputs beginning with `=` are treated as plain text unless explicitly typed as `formula` in spec.
- **Locked Zones (FR-09)**: Writes targeting locked ranges are rejected immediately with `E-LOCK-001`.
- **Text Normalization (SEC-02)**: Unicode NFC normalization; strip XML 1.0 invalid control characters (`\x00..\x08`, `\x0B..\x0C`, `\x0E..\x1F`).
- **Macro & External Link Rejection (SEC-03)**: Reject `.xlsm`, `vbaProject.bin`, OLE objects, and external links (`E-SEC-MACRO`, `E-SEC-EXTLINK`).

---

## 7. Two-Tier Validation Architecture (UG & PG)

1. **13 Universal Gates (UG-01..13)** — Mandatory for all workbooks:
   - `UG-01`: Valid OOXML package, opens cleanly without repair alerts.
   - `UG-02`: Package Inventory Parity (zero silent dropping of images, charts, CF, DV, tables).
   - `UG-03`: Formula integrity (functions/strings preserved; summaries are live formulas).
   - `UG-04`: Zero recalculation errors (`#REF!`, `#NAME?`, `#DIV/0!`, `#VALUE!`).
   - `UG-05`: Style signatures match prototype row 100% (font, fill, border, format).
   - `UG-06`: Non-overlapping merged cells, Top-Left value assignment, synchronized borders.
   - `UG-07`: Positional dependencies consistently shifted with data.
   - `UG-08`: Warning scans for `###` overflow risks or clipped text.
   - `UG-09`: Identifier columns enforce `number_format='@'` and preserve leading zeros.
   - `UG-10`: Zero lingering placeholders (`{{...}}`, `<...>`).
   - `UG-11`: Geometric and stylistic symmetry across Sibling Sheets.
   - `UG-12`: Security sanitization (zero macros, zero untrusted external links).
   - `UG-13`: Cache consistency (data_only matches values_summary, `<f>` tags intact).
2. **Profile Gates (PG)**: Domain-specific rule profiles (e.g., `unit_test_matrix` enforcing PG-UT-01..12).

---

## 8. Operational Triage & Exit Codes

- **CLI/CI Exit Codes**: `0` = 100% clean; `1` = Cosmetic warning or style deviation (`W-DEV-*`); `2` = Critical error (`E-*`).
- **Handling `W-DEV-*`**: Halt, preserve template baseline, and prompt user via `/grill-me`. Never impose arbitrary stylistic changes.

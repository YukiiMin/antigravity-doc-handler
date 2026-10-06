---
name: excel-handler
description: Master operations guide, mental model, and decision tree for XLSX Engine and universal spreadsheet processing (Excel .xlsx, .xls). Xử lý bảng tính Excel, dịch công thức AST, bảo toàn logo DrawingML, tiêm cache Recalc lxml, kiểm định 13 Universal Gates UG, đối soát diff.
---

# Antigravity Skill: XLSX Engine & Universal Spreadsheet Handler (`excel-handler`)

Use this skill whenever you need to create, inspect, mutate, validate, recalculate, or diff Excel workbooks (`.xlsx`, `.xls`) based on enterprise templates or generated from `XlsxSpec`.

> **Mandatory Standard**: See [rule_xlsx_engine_standards.md](file:///d:/Minh/For_myself/ZSCORT_GSU26_SAP05/tool/pdf_to_docx_converter/.agents/rules/rule_xlsx_engine_standards.md) for invariants E1–E14, `ERR_XLSX_001..007`, Shift invariants, and the Grill-Before-Deviate protocol.  
> **Delivery & Git Protocol**: Follow the Micro-Commit Cadence (`X.Y.Z`) and Git standards in `doctools-delivery`.

---

## 🧠 Core Philosophy & Mental Model

### 1. Deterministic Engine, Decisive AI
- **The engine is a deterministic MCP server**: It never invokes AI to summarize metrics, contains zero hidden prompts, and never stretches styling without explicit spec or manifest declarations.
- **The AI client is the orchestrator**: Analyzing user goals, inspecting workbook hierarchy via `inspect_xlsx`, emitting precise `MutationSpec` JSON, triaging `diagnostics`, and seeking human approval upon template deviation warnings (`W-DEV-*`).

### 2. Template is Ground Truth & Original Immutability
- **Never hardcode styles**: Every formatting token (font, fill rgb/theme/indexed, border, alignment, `wrap_text`, number format `@`) must clone directly from a **Prototype Row** or extract from a **Reference Sheet** (`Example`, `Template`, `Sample`, `Pattern`).
- **Original Immutability (NFR-08)**: All mutations (`mutate_xlsx`, `recalc_xlsx`) execute on isolated temporary working copies. The original file preserves 100% of its `sha256` hash. Modified workbooks are delivered via opaque `FileRef` handles.

### 3. Dual-Path Builder Architecture
- **Path A — Mutate Template (Path A: openpyxl + Atomic Clone & Shift)**:
  - For workbooks with baseline templates (Report5 matrices, timesheets, financial models).
  - Accepts declarative `MutationSpec` JSON: `cell_updates`, `table_expansions` (with anchor, `prototype_row`, `id_columns`), `freeze_panes`, and `calc_policy`.
- **Path B — XlsxSpec Path (Path B: XlsxWriter + Design Tokens)**:
  - For brand new workbooks generated from scratch without templates.
  - Employs standardized Design Tokens (`Theme.PRIMARY`, `Border.accounting_double`) and formula-driven conditional formatting (e.g., `=MOD(ROW(),2)=0`).

### 4. Single Shift Manager Path via AST Tokenizer (D-03, D-04, FR-07)
- **Strict Prohibition on Full-String Regex (P-01, P-02)**: Parse formulas via `openpyxl.formula.Tokenizer`. **Shift only cell and range operands pointing to target sheets**. Preserve 100% of function names (`LOG10`, `DAYS360`), string literals (`"TC001"`), and identifiers (`FY2024`).
- **Co-Shifted Dependencies in a Single Pass**: Workbook formulas, merged cells, CF/DV `sqref`, ListObject table and AutoFilter `ref`, Defined Names, Print Areas, Chart series & anchors, row heights.
- **Range Policy**: `table_aware` expands summary ranges when inserting at boundaries; `excel_native` keeps ranges pinned during raw inserts.
- **Orphan Reference Guard**: Deleting rows/columns that destroy reference targets raises `E-SHIFT-ORPHAN` immediately, preventing silent `#REF!` corruption.

### 5. Recalc Backend & Cache Writer (`write_cached` via `lxml`, EV-13)
- **Eliminating Blank Formula Values (P-05)**: openpyxl saves workbooks without `<v>` cached value elements, causing pandas, openpyxl `data_only=True`, and Windows Explorer preview to show empty cells.
- **Standard Pipeline**:
  1. Dispatch working copy to Recalc Backend (LibreOffice headless in sandbox) to recompute and scan for errors (`#REF!`, `#DIV/0!`).
  2. Use `lxml` to patch `xl/worksheets/sheetN.xml`: inject `<v>` nodes and type attributes `t` (`n`/`str`/`b`/`e`) for `<c>` nodes with `<f>`.
  3. Preserve 100% of live `<f>` formula tags.
  4. Self-verify via Gate `UG-13`: re-reading via `data_only=True` must match `values_summary` exactly.

### 6. Two-Tier Validation & Structural Diff (D-07, D-08)
- **Universal Gates (UG-01..13)**: Mandatory for all workbooks (OOXML validity, inventory parity, formula integrity, zero recalculation errors, prototype style cloning, safe merges, security sanitization, cache consistency).
- **Profile Gates (PG)**: Declared per template profile (e.g., `unit_test_matrix` inheriting Report5 quality gates).
- **Structural Diff (`xlsx.diff`)**: Compares Package Inventory before and after mutations, flagging undeclared losses.

---

## 🌲 Decision Tree & Use Cases

```
                                  [Spreadsheet Task]
                                          │
         ┌────────────────────────────────┼────────────────────────────────┐
         ▼                                ▼                                ▼
  [Template Onboarding]           [Mutate Template]               [Validate & Diff]
         │                                │                                │
  ┌──────┴──────┐                  ┌──────┴──────┐                  ┌──────┴──────┐
  ▼             ▼                  ▼             ▼                  ▼             ▼
xlsx.preflight  xlsx.lint_template xlsx.inspect  xlsx.mutate        xlsx.validate  xlsx.diff
(Inventory)     (Anchor/Zones)     (Anchors/Val) (Shift+Style)      (UG + PG)      (Declared?)
         │                                │                                │
         ▼                                ▼                                ▼
 xlsx.register_template            xlsx.recalc (Cache)             xlsx.repair (P1)
 (YAML Manifest)                   -> Final FileRef                (Fix Engine Issues)
```

### Case 1: Template Onboarding
1. Call `xlsx.preflight(file_ref)` to inspect Package Inventory and determine Fidelity Tier (T1/T2/T3).
2. Call `xlsx.lint_template(template_ref)` to inspect anchors, Prototype Rows, locked zones, and lingering placeholders.
3. Draft manifest YAML (`anchors`, `prototype_rows`, `locked_zones`, `id_columns`, `calc_policy`, `gates_profile`).
4. Call `xlsx.register_template(template_ref, manifest)` to record version and `sha256` hash.

### Case 2: Mutating Existing Templates (Path A Mutation)
1. Call `xlsx.inspect(file_ref)` to retrieve structural snapshot, active anchors, and `values_status`.
2. Draft `MutationSpec` JSON:
   - Declare `table_expansions` with anchor header text, `prototype_row`, `rows[]`, and `id_columns` (`@` format).
   - Configure `calc_policy: { recalc: "oracle_verify", cache: "write", calc_on_open: "auto" }`.
   - If proposing UX improvements that diverge from template: Confirm via `/grill-me` and record in `approved_deviations[]`.
3. Call `xlsx.mutate(template_id, mutation_spec)` $\rightarrow$ Engine executes Shift Manager, clones styles, recomputes, and injects cache.
4. Inspect returned envelope: extract output `file_ref` and review `diagnostics`.

### Case 3: Creating Workbooks from Scratch (Path B XlsxSpec)
1. AI drafts `XlsxSpec` JSON (sheets, tables, columns, rows, cell types).
2. Specify Design Tokens by name (`theme: "corporate_blue"`, `border: "thin_grid"`). Never invent arbitrary hex colors.
3. Call `xlsx.build(xlsx_spec)` $\rightarrow$ Engine compiles via XlsxWriter, calculates formulas, and delivers file.

### Case 4: Validation & Quality Assurance
1. Call `xlsx.validate(file_ref, profile="unit_test_matrix")` to verify 13 UG Gates and Profile Gates.
2. Call `xlsx.diff(file_ref_a, file_ref_b)` to diff pre- and post-mutation package inventories.
3. If errors are marked `fixable_by="engine"`: Call `xlsx.repair(file_ref, issues=[...])` for deterministic remediation.

---

## 💻 Core MCP Tool Catalog (`xlsx.*`)

All tools communicate via `FileRef` handles `{ uri, sha256, size, mime, expires_at }` and return standard envelopes `{ success, file_ref, diagnostics, guarantees_applied, stats }`.

| Tool Name | Mode | Primary Input | Primary Output |
|---|---|---|---|
| `xlsx.preflight` | Read-only | `file_ref` | `inventory`, `fidelity_tier`, `issues` |
| `xlsx.inspect` | Read-only | `file_ref`, `sheet?`, `range?` | Tree, cells, formulas, `values_status` |
| `xlsx.lint_template` | Read-only | `template_ref` | `valid`, `anchors_found`, `issues` |
| `xlsx.register_template` | Admin | `template_ref`, `manifest` | `template_id`, `version`, `manifest` |
| `xlsx.list_templates` | Admin | — | List of registered templates |
| `xlsx.get_template_manifest` | Admin | `template_id` | YAML manifest definition |
| `xlsx.mutate` | Execute | `template_id`/`file_ref`, `mutation_spec` | New `file_ref`, `diagnostics`, `stats` |
| `xlsx.build` | Execute | `xlsx_spec` | New `file_ref`, `diagnostics` |
| `xlsx.recalc` | Execute | `file_ref`, `calc_policy?` | `values_summary`, `errors`, cached `file_ref` |
| `xlsx.validate` | Validate | `file_ref`, `profile?` | `issues`, `gates_passed`, `gates_failed` |
| `xlsx.diff` | Validate | `file_ref_a`, `file_ref_b` | Package inventory and styled differences |

---

## 🛡 Diagnostics Triage & Error Remediation

```
Receive Diagnostics
  ├─ Contains Errors?
  │     ├─ E-PKG-*   (Corrupt OOXML)          ──► Halt, alert user / change template
  │     ├─ E-LOCK-*  (Writing to locked zone) ──► Halt immediately, do NOT overwrite, ask user
  │     ├─ E-SHIFT-* (Shift/orphan error)     ──► Halt, do not deliver file, analyze evidence
  │     ├─ E-CACHE-* (Cache type/XML error)   ──► Halt, core engine bug, report details
  │     └─ E-SPEC-*  (Invalid spec schema)    ──► AI auto-fixes spec via JSON path (max 2 attempts)
  │
  └─ Contains Warnings?
        ├─ W-PKG-UNSUPPORTED-* (Shape/Slicer) ──► Halt, ask user: accept loss or alter template
        ├─ W-DEV-* (Template deviation)       ──► Halt, present diff via /grill-me for approval
        ├─ W-CALC-* (Volatile/uncomputed)     ──► Deliver file with data origin notes
        └─ W-LAYOUT / W-STYLE (estimated)     ──► Refine spec or accept if compliant
```

### Common Error Codes & Suggested Actions

| Error Code | Technical Cause | AI Automated Remediation (`suggested_action`) |
|---|---|---|
| `E-LOCK-001` | Write targets cells inside manifest `locked_zones` | Strip target cell from `cell_updates`; adjust table expansion anchor |
| `E-SHIFT-002` | Cross-sheet formula unshifted after row insert | Rerun Shift Manager with explicit `target_sheet` parameter |
| `E-SHIFT-ORPHAN` | Row/col deletion destroyed formula reference | Revert deletion or update formula reference prior to delete |
| `E-TPL-ANCHOR-AMBIGUOUS` | Found >1 matching cells for anchor keyword | Narrow `scan_rows` or set `scope: "first_table"` |
| `E-CACHE-TYPE-MISMATCH` | data_only cache does not match Recalc value | Inspect type mapping in Cache Writer (`n`/`str`/`b`/`e`) |
| `W-DEV-LAYOUT:freeze_panes`| Proposed freeze panes diverge from template | Ask user via `/grill-me`. If approved, append code to `approved_deviations` |
| `W-PKG-UNSUPPORTED-SHAPE`| Template contains shapes vulnerable to loss | Confirm risk with user before executing save |
| `W-CALC-NO-CACHE` | Unsupported complex formula in Recalc Backend | Deliver file with `calc_on_open: "on"` for Excel client-side evaluation |

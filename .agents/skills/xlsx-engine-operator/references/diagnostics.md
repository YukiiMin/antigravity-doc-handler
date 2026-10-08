# Diagnostic Codes & Worked Remediation Guide

This reference explains the most critical diagnostics emitted by the `xlsx.*` engine, how to triage them by `fixable_by`, and how to resolve them without compromising document logic.

---

## 1. The EV-15 Empirical Lessons (Real-world Defect Playbooks)

### `W-FORMULA-EMPTY-CELL-REF` & `W-XLSX-UG16-EMPTY-CELL-REF`
* **Trigger**: A mathematical formula references a cell that is empty (`value is None`) at build time.
* **Severity**: `WARNING` | **`fixable_by`**: `ai` (if intent is unambiguous) or `human` (if ambiguous).
* **The Root Cause (EV-15.3)**:
  In `Report5` matrix, `Return(Staff)!L4` had:
  ```excel
  =IF(Functions!E6<>"N/A", SUM(C4*Functions!E6/1000, -AA7), "N/A")
  ```
  `AA7` was completely blank (evaluating to $0$). The formula evaluated to $+12$ or $+15$ instead of $12 - 22 = -10$ because it never subtracted the 22 tests written below. The author mistyped `-AA7` instead of `-O7` (where cell `O7` held the actual test count).
* **Correct Action**:
  1. Never delete the formula or replace it with a static constant.
  2. Inspect the reference sheet (`Example`) or sibling rows: find which cell holds the actual quantity.
  3. Update the formula via `xlsx.mutate` to point to the correct data cell (e.g., `-O7`).
  4. Note the fix explicitly in your final report.

---

### `E-XLSX-UG14-VALIDATION-DROPPED`
* **Trigger**: A newly cloned or mutated worksheet has 0 Data Validations while the reference sheet or template manifest specifies active validations (e.g., dropdown list for `"O"` or `"PASS,FAIL"`).
* **Severity**: `ERROR` | **`fixable_by`**: `engine` or `ai`.
* **The Root Cause (EV-15.1)**:
  `openpyxl.copy_worksheet()` silently drops `ws.data_validations`, stripping dropdown arrows and turning interactive selection cells into plain dead text.
* **Correct Action**:
  1. Do not use native openpyxl copy scripts.
  2. Use the engine's built-in `xlsx.copy_sheet` (powered by `SheetCloner`), which independently copies `DataValidation` and `ConditionalFormatting` rules and re-wires self-referencing formulas.
  3. If validations are already missing on an existing sheet, use `xlsx.set_validation` to re-attach the list rule to the required cell range (e.g. `formula1='"O"'`).

---

### `W-XLSX-BORDER-GAP` & `W-XLSX-UG15-INCONSISTENT-BORDERS`
* **Trigger**: A table cell inside a data block is missing borders on sides where the Prototype Row has active borders.
* **Severity**: `WARNING` | **`fixable_by`**: `engine` (via explicit policy) or `human`.
* **The Root Cause (EV-15.2)**:
  In `Statistics`, row 12 had full `hair` borders, but rows 13..18 were missing column B-C borders, and rows 19..21 had no borders. When AI cleared `#REF!` values, blank un-bordered patches appeared.
* **Correct Action**:
  1. Do NOT guess and silently apply borders ("Template is ground truth").
  2. If the user requests fixing template table styling, set `border_policy: "inherit_prototype"` in your `MutationSpec` or call `xlsx.mutate`.
  3. The engine will safely clone prototype row borders to the unbordered cells and log `I-XLSX-BORDER-REPAIRED` in diagnostics.

---

## 2. Core Structural & Shift Diagnostics

### `E-SHIFT-ORPHAN` / `E-XLSX-UG03-FORMULA-ERROR` (`#REF!`)
* **Trigger**: A row/column was deleted or shifted, destroying the reference target of another formula.
* **`fixable_by`**: `ai`.
* **Correct Action**:
  - Never silence `#REF!` by setting `cell.value = 0` or deleting the cell unless the user explicitly requested clearing deleted series.
  - Trace the source sheet and recalculate the reference.

---

### `E-LOCK-001`
* **Trigger**: MutationSpec attempted to write into a cell declared inside `locked_zones` (e.g. `Statistics!C12:I19` or `*!A1:T8`).
* **`fixable_by`**: `ai`.
* **Correct Action**:
  - Check the cell coordinate against the manifest locked zones.
  - Remove the coordinate from `cell_updates` or move table expansion anchors to allowable data zones.

---

### `W-DEV-LAYOUT:*` / `W-DEV-STYLE:*`
* **Trigger**: Spec requested layout adjustments (like changing freeze panes or column widths) that diverge from the reference template.
* **`fixable_by`**: `human`.
* **Correct Action**:
  - Stop and ask the user for confirmation.
  - If approved, pass the deviation code in `approved_deviations: ["W-DEV-LAYOUT:freeze_panes"]`.

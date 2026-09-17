# Rule: Spreadsheet Template Preservation — Template-Driven Format Extraction & Grill-Before-Deviate

> **Scope**: Universally applies when reading, mutating, styling, or populating data into any Spreadsheet Template
> (Excel `.xlsx`, `.xls`, LibreOffice Calc, Google Sheets, or OpenPyXL / XlsxWriter / Pandas pipelines).

---

## 1. Core Invariants

| # | Invariant | What Violation Looks Like | Corrective Principle |
|---|---|---|---|
| **E1** | **Template-Driven Format Extraction** | Hardcoding `font='Tahoma'`, `size=12`, `fill='#000080'` in generation scripts or rules based on one-time observation. | Extract ALL format tokens from the reference sheet inside the workbook. Never guess or hardcode style values. |
| **E2** | **Grill-Before-Deviate** | Adding freeze panes, color badges, typography changes, or UX improvements without user consent. | STOP → list every proposed deviation from template → ask user via `/grill-me` BEFORE applying anything non-trivial. |
| **E3** | **Live Dynamic Cross-Sheet Formulas** | Hardcoded numbers in Summary/Statistics/Dashboard sheets (`Passed: 3`). | All KPI/summary cells MUST be live formulas: `='Sheet'!Cell`, `=COUNTIF(...)`, `=SUM(...)`, `=IF(...)`. |
| **E4** | **Chronological & Domain-Relevant Mock Data** | Retaining obsolete placeholder years (`2000`, `2007`, `2009`) from legacy template skeletons. | Inject mock data aligned to the project's current operational era and technology domain. |
| **E5** | **Sibling Structural Symmetry** | Parallel tabs sharing the same schema having inconsistent column widths, row heights, freeze panes, or styling. | Sibling sheets must have 100% matched geometry and style rules — derived from the same reference sheet. |

---

## 2. Template-Driven Format Extraction (The Golden Method)

**Principle**: The workbook's own `Example`, `Template`, `Sample`, or `Pattern` sheet is the **single source of truth** for all formatting decisions. Code and rules must NEVER substitute their own values.

### Step-by-Step Protocol

```python
from copy import copy
import openpyxl

wb = openpyxl.load_workbook(template_path, data_only=False)

# 1. Identify the reference sheet (Example / Template / Sample / Pattern)
ref_sheet_name = next(
    (s for s in wb.sheetnames if s.lower() in ["example", "template", "sample", "pattern"]),
    None
)
if not ref_sheet_name:
    raise RuntimeError("No reference sheet found. Cannot proceed without format source of truth.")

ws_ref = wb[ref_sheet_name]

# 2. Locate reference cells for each element type
ref_mark_cell   = ws_ref["F15"]  # First 'O' selection mark in the matrix
ref_header_cell = ws_ref["F9"]   # First test-case header (Row 9)
ref_section_a   = ws_ref["A10"]  # Column A section title (Condition)

# 3. Extract format tokens — NO hardcoding
MARK_FONT      = copy(ref_mark_cell.font)
MARK_ALIGNMENT = copy(ref_mark_cell.alignment)
MARK_BORDER    = copy(ref_mark_cell.border)

HEADER_FONT      = copy(ref_header_cell.font)
HEADER_FILL      = copy(ref_header_cell.fill)
HEADER_ALIGNMENT = copy(ref_header_cell.alignment)

SECTION_FONT      = copy(ref_section_a.font)
SECTION_FILL      = copy(ref_section_a.fill)
SECTION_ALIGNMENT = copy(ref_section_a.alignment)

# 4. Apply extracted tokens to ALL equivalent cells in target sheets
for col_idx, tcid in enumerate(test_case_ids, start=6):
    col = get_column_letter(col_idx)
    ws.cell(9, col_idx).font      = copy(HEADER_FONT)
    ws.cell(9, col_idx).fill      = copy(HEADER_FILL)
    ws.cell(9, col_idx).alignment = copy(HEADER_ALIGNMENT)
    # ... for mark cells:
    ws[f"{col}15"].font      = copy(MARK_FONT)
    ws[f"{col}15"].alignment = copy(MARK_ALIGNMENT)
```

### Fallback (No Reference Sheet Exists)
1. Read format tokens from the **first populated equivalent cell** in the most complete sibling sheet.
2. Document the extracted values as a comment block in the generation script for traceability.
3. NEVER invent or guess values — always trace back to an observable source in the actual file.

---

## 3. Grill-Before-Deviate Protocol

**Invariant**: When AI identifies an opportunity to improve UX in a way that **deviates** from the template
(adding color badges, changing typography, adjusting borders, inserting freeze panes), it MUST:

1. **STOP** — do NOT apply the change.
2. **List** proposed deviations explicitly:
   > "I want to change X from [extracted template value] to [proposed value] because [reason]."
3. **Ask user** via `/grill-me` before proceeding.
4. Only apply changes with **explicit user approval**.

**Exception** — approval NOT required for:
- Filling empty data cells with content (no style change).
- Adding content to cells that are empty in the template and have no defined style.

---

## 4. Dynamic Cross-Sheet Formula Reference Patterns

### Detail Sheet Aggregates (example — adapt column range to actual data range)
```
Passed:   =COUNTIF(<StatusRow_range>, "P")
Failed:   =COUNTIF(<StatusRow_range>, "F")
Untested: =SUM(<Total>, -<Passed>, -<Failed>)
Total:    =COUNTA(<HeaderRow_range>)
N/A/B:    =COUNTIF(<TypeRow_range>, "N")  /  "A"  /  "B"
```

### Summary Sheet Binding
```
='<DetailSheet>'!<PassedCell>         # Direct cell reference
=SUM(<DetailRow_range>)               # Subtotal
=IF(<Total>=0, 0, <Pass>/<Total>*100) # KPI ratio (division-by-zero guarded)
```

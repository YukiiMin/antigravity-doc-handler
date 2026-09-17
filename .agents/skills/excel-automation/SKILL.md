---
name: excel-automation
description: Master operations guide, mental model, and best practices for high-fidelity Excel template processing using Template-Driven Format Extraction. Covers in-place openpyxl mutation, reference sheet format token extraction, cross-sheet dynamic formula linking, Grill-Before-Deviate protocol, and legacy XLS dual-delivery.
---

# Antigravity Master Skill: Universal Excel Automation & Template Engineering (`excel-automation`)

Use this skill whenever you need to process, inspect, mutate, style, or generate publication-grade Excel spreadsheets (`.xlsx`, `.xls`) from templates without breaking author visual signatures or losing embedded DrawingML images.

> **Invariants**: See `rule_excel_template_preservation_and_ux.md` for format extraction rules and Grill-Before-Deviate protocol.

---

## 🧠 Core Mental Model

### 1. Template-Anchored In-Place Mutation
Never build complex multi-sheet corporate workbooks from a blank sheet (`openpyxl.Workbook()`).

**The Golden Method**:
```python
wb = openpyxl.load_workbook(template_path, data_only=False)
# 1. Locate reference sheet (Example / Template / Sample / Pattern)
# 2. Extract format tokens from reference cells
# 3. Mutate target data cells in-place using extracted tokens
# 4. Save to output path
wb.save(output_path)
```

### 2. Template-Driven Format Extraction (NOT Hardcoding)

**WRONG** — hardcoded, will break when template changes:
```python
cell.font = Font(name='Tahoma', size=12, bold=True)  # ❌ learned vẹt
```

**CORRECT** — derived from the workbook's own reference sheet:
```python
from copy import copy
ws_ref = wb["Example"]           # or "Template" / "Sample" / "Pattern"
ref_mark = ws_ref["F15"]         # first 'O' mark cell
MARK_FONT      = copy(ref_mark.font)
MARK_ALIGNMENT = copy(ref_mark.alignment)
MARK_BORDER    = copy(ref_mark.border)
# Now apply MARK_FONT to all equivalent cells — zero hardcoded overrides
```

### 3. Reference Cell Discovery Pattern
When locating reference cells in an Example sheet:
```python
def find_first_mark_cell(ws_ref, mark_value="O", row_start=10, row_end=42, col_start=6):
    """Locate the first cell containing mark_value in the data matrix."""
    for r in range(row_start, row_end + 1):
        for c in range(col_start, ws_ref.max_column + 1):
            if ws_ref.cell(r, c).value == mark_value:
                return ws_ref.cell(r, c)
    return None
```

### 4. Merged Cell Safety Protocol
Directly writing to a merged cell coordinate corrupts the worksheet XML:
```python
def safe_set_cell(ws, coordinate, value=None, formula=None, **styles):
    cell = ws[coordinate]
    if isinstance(cell, openpyxl.cell.cell.MergedCell):
        for m_range in ws.merged_cells.ranges:
            if coordinate in m_range:
                coordinate = m_range.coord.split(":")[0]
                break
    cell = ws[coordinate]
    if formula and str(formula).startswith("="):
        cell.value = formula
    elif value is not None:
        cell.value = value
    for attr, val in styles.items():
        if val is not None:
            setattr(cell, attr, val)
```

### 5. Dynamic Real-Time Formulas (Never Hardcode Aggregates)
Summary/Statistics sheets MUST use live cross-sheet formulas:
```python
# Passed count from child sheet
ws_stat["C12"].value = "='Function 1'!A7"
# Subtotal
ws_stat["C17"].value = "=SUM(C12:C14)"
# Division-by-zero guarded KPI ratio
ws_stat["D19"].value = "=IF(I17=0, 0, (C17+D17)/I17*100)"
```

### 6. Grill-Before-Deviate
Any UX improvement deviating from the template (freeze panes, color badges, border style changes) requires:
1. **STOP** — do not apply.
2. **List** deviations explicitly with before/after values and rationale.
3. **Ask user** via `/grill-me` first.
4. Apply only with explicit user approval.

---

## 💻 CLI & Python Execution Patterns

### Pattern A: Extract & Inspect Format Tokens from Reference Sheet
```bash
python tools/inspect_example_tokens.py
```

### Pattern B: Generate Template-Driven Enhanced Excel Deliverable
```bash
python tools/generate_enhanced_ux_excel.py
```

### Pattern C: Export Legacy Binary XLS via LibreOffice Headless
```bash
soffice --headless --convert-to xls "dataset1/output/Report5_Unit Test_Enhanced_UX.xlsx" --outdir "dataset1/output/"
```

### Pattern D: Validate Quality Gate (Zero Placeholders + Formula Integrity)
```python
from tools.generate_enhanced_ux_excel import validate_unit_test_workbook
validate_unit_test_workbook("dataset1/output/Report5_Unit Test_Enhanced_UX_v2.xlsx")
```

---

## 🛡 Quality Gate Checklist Before Delivery

- [ ] Zero unreplaced placeholders (`<...>`, `{{...}}`) — regex scan.
- [ ] DrawingML logo preserved (`len(ws._images) > 0` on Cover sheet).
- [ ] All summary cells contain live formulas starting with `=`.
- [ ] Reference sheet format tokens were extracted — NOT hardcoded.
- [ ] Both `.xlsx` and `.xls` exist in output directory with non-zero size.
- [ ] Deviations from template were approved by user via `/grill-me`.

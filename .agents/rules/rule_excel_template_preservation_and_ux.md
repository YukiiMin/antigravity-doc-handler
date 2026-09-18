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
| **E6** | **Automated Format Diff Before Delivery** | Declaring "SUCCESS" or delivering output based solely on `exit code 0` without verifying format attributes. | ALWAYS run a programmatic diff (cell-by-cell: font, fill, border, alignment, col width, row height, merges, DVs) across all 12 Quality Gates between the generated sheet and the reference sheet BEFORE presenting output to user. Workflow: `generate → diff → fix → diff → (clean) → deliver`. Forbidden: `generate → exit 0 → deliver`. |
| **E7** | **Multi-Column Unified Box Geometry** | Calling cell style setters only on populated cells, leaving empty cells unstyled or creating internal vertical divider lines between columns that visually form a single box. | Initialize the full multi-column block (e.g. cols B-C-D) across EVERY data row before populating text: B (left=thin, right=None), C (left=None, right=None, horizontal borders only), D (left=None, right=thin), all filled solid white (`FFFFFFFF`). |
| **E8** | **Strict Group-Detail Hierarchy** | Repeating the group header name on subsequent child rows (e.g. 'Precondition' in row 10 and row 11). | Group titles must strictly appear ONLY in the first row of that group (Col B). All subordinate sibling rows MUST leave Col B empty and place descriptions in Col D. |
| **E9** | **Cross-Zone Token Isolation** | Reusing a sub-item style token (e.g. B34 `list ` with `bold=True, align=right`) for Result footer labels (B45..B48) or summary labels. | Extract tokens strictly on a per-zone basis directly from the exact corresponding row of the reference sheet (`ws_ref.cell(r, c)`). Never generalize a sub-item style across different structural blocks. |
| **E10** | **Multi-Tier Hierarchy Preservation** | Collapsing input parameters directly under Precondition or omitting the Level-2 parameter group header in Col B when mapping from flat test specification data. | Preserve the full 3-tier hierarchy: Level 1 (`Precondition` in B10), Level 2 (`Input Parameters` / `ParamName` in Col B), Level 3 (Concrete values in Col D). |
| **E11** | **Untrusted Input Style Isolation** | Copying font family, font size, or colors from input data sheets (e.g. input using Arial 8.5pt shrinks summary tables). | Raw input files are **UNTRUSTED** for style. Extract ONLY raw values (`cell.value`). 100% of format tokens (fonts, sizes, fills, borders, alignments) MUST be sampled from the Template. |
| **E12** | **Dynamic Chart Re-Anchoring & Relinking** | Cloning template sheets containing charts without updating static series formulas (`numRef.f`) or repositioning chart anchors when row counts change. | OpenPyXL does NOT auto-rewrite chart formula strings. Script must explicitly relink `chart.series[].val.numRef.f` to the new Subtotal row and reposition `chart.anchor._from.row` below all summary tables. |
| **E13** | **UX Dynamic Text Auto-Scaling** | Using fixed row heights for multi-line description cells causing text clipping, overflow into adjacent matrix columns, or truncation. | Apply dynamic row height calculation: `Row Height = max(min_h, total_lines * line_h)` based on character length and `\n` linebreaks, with `wrap_text=True` enabled on all descriptive text blocks. |
| **E14** | **Summary & Subtotal Regional Parity** | Painting solid accent color across entire subtotal row or omitting ratio KPI metrics present in the template. | Respect regional subtotal styling: dark accent fills for labels and grand total columns; transparent/white fill with standard text font for aggregate value cells. Preserve 100% of template ratio KPI rows. |

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

---

## 5. Mandatory Pre-Delivery Format Diff Protocol (E6)

**Invariant E6**: After ANY Excel generation or mutation task, AI MUST run automated format validation before declaring output ready. `exit code 0` alone is NOT sufficient proof of format correctness.

### When to trigger
- After any `wb.save()` that produces a new or modified sheet with format requirements.
- After copying a reference/template sheet and injecting new data.
- After running any Excel generation script.

### The 12 Mandatory Quality Gates

| # | Quality Gate | Verification Protocol |
|---|---|---|
| **1** | **Header Block (Rows 2–8)** | Cell-by-cell `font`, `size`, `bold`, `fill`, `alignment`, `border`, `number_format` across A2..T8. |
| **2** | **Row 7 KPI Formulas** | Dynamic formulas (`=COUNTIF`, `=SUM`, `=COUNTA`) on A7, C7, F7, L7, M7, N7, O7. No hardcoded numbers. |
| **3** | **Row 9 TC Headers** | Col A navy+double border; Cols B-E navy+border top; Cols F+ rotated 180°, double border top, TC IDs. |
| **4** | **Col A Continuous Navy Fill** | Unbroken `FF000080` navy fill across all data rows (no gaps) + `border_left='double'`. |
| **5** | **Col B-C-D Unified Box** | 3-column unified box per row: B (`left=thin, right=None`), C (`left=None, right=None`), D (`left=None, right=thin`), solid white fill `FFFFFFFF`. |
| **6** | **Duplicate Header Detection** | Automated alert if Col B duplicates header text on consecutive rows. |
| **7** | **Matrix Grid & O-Marks** | Grid borders (`thin`) on all matrix cells; O-marks with correct font/bold/alignment. |
| **8** | **Result Section Typography** | Courier non-bold 8pt for Type/PF; Tahoma 8pt `textRotation=255` & `mm/dd` numfmt for Executed Date. |
| **9** | **Merged Cells Validation** | Exact Header merges (`A2:B2`, `C2:E2`, `F2:K2`, `L2:T2`) and Result footer merges (`B:D`). |
| **10** | **Section Closing Borders** | Double bottom border on Condition last row (`Side(style='double')`) and Result last row. |
| **11** | **Data Validations** | Dropdowns for `"O"` on matrix, `"N,A,B"` on Type row, `"P,F"` on PF row. |
| **12** | **Geometry & Overflow Guards** | Exact col widths & row heights (R9=45.0, data=13.5) + Col D text overflow guard. |

### Mandatory workflow
```
generate_output() → run_format_diff() → if diffs_found → fix() → run_format_diff() → if clean → deliver_to_user()
```

### FORBIDDEN anti-pattern
```
generate_output() → exit_code == 0 → "SUCCESS" → deliver_to_user()  ← WRONG
```

---

## 6. Multi-Column Unified Box & Hierarchy Code Patterns (E7, E8)

### Row Initialization for Unified 3-Column Boxes
```python
# Condition block initialization
for r in range(COND_START, CONF_START):
    is_last = (r == CONF_START - 1)
    b_side = Side(style='double') if is_last else Side(style='thin')
    
    # Col B: Left border only, NO right vertical divider
    apply(ws.cell(r, 2), font=t['b_top_font'], fill=t['b_top_fill'], align=t['b_top_align'],
          border=Border(left=Side(style='thin'), top=Side(style='thin'), bottom=b_side))
    # Col C: Internal cell, horizontal borders only
    apply(ws.cell(r, 3), font=t['b_top_font'], fill=t['b_top_fill'], align=t['b_top_align'],
          border=Border(top=Side(style='thin'), bottom=b_side))
    # Col D: Right border only, NO left vertical divider
    apply(ws.cell(r, 4), font=t['d_top_font'], fill=t['d_top_fill'], align=t['d_top_align'],
          border=Border(right=Side(style='thin'), top=Side(style='thin'), bottom=b_side))
```

### Strict Group-Detail Data Population
```python
# Group header row (Row 10): Name in Col B, Col D empty
ws.cell(10, 2).value = 'Precondition'
ws.cell(10, 4).value = None

# Detail sub-rows (Rows 11-13): Col B empty, descriptions in Col D
ws.cell(11, 2).value = None
ws.cell(11, 4).value = 'User is authenticated (valid JWT token)'

ws.cell(12, 2).value = None
ws.cell(12, 4).value = 'Product catalog is loaded (>0 items)'
```

---

## 7. Untrusted Input Style Isolation (E11)

**Principle**: Raw input files provided by users or external systems are strictly for **data ingestion only**. They frequently contain corrupted font sizes (e.g. Arial 8.5pt), inconsistent fills, broken merges, or lost number formats.

```python
# BAD: Cloning cell style from input data
ws_target.cell(r, c).font = copy(ws_input.cell(r, c).font)  # NEVER do this!

# GOOD: Read ONLY values from input, apply styles from Template Tokens
raw_val = ws_input.cell(r, c).value
ws_target.cell(r, c).value = raw_val
apply(ws_target.cell(r, c), font=template_tokens['data_font'], fill=template_tokens['data_fill'])
```

---

## 8. Dynamic Chart Re-Anchoring & Series Relinking in OpenPyXL (E12)

**Principle**: OpenPyXL does NOT automatically update chart formula strings (`numRef.f`, `strRef.f`) when table rows are inserted, deleted, or expanded. Any script modifying table bounds MUST relink charts explicitly.

```python
# Relink charts to dynamic subtotal row
for chart in ws.charts:
    for s in chart.series:
        if s.val and s.val.numRef:
            f_str = s.val.numRef.f or ''
            if 'F' in f_str:
                s.val.numRef.f = f"{sheet_name}!$F${SUB_ROW}:$H${SUB_ROW}"
                if s.cat and s.cat.strRef:
                    s.cat.strRef.f = f"{sheet_name}!$F$11:$H$11"
            elif 'C' in f_str:
                s.val.numRef.f = f"{sheet_name}!$C${SUB_ROW}:$E${SUB_ROW}"
                if s.cat and s.cat.strRef:
                    s.cat.strRef.f = f"{sheet_name}!$C$11:$E$11"

    # Reposition chart anchor below summary tables
    if hasattr(chart.anchor, '_from'):
        chart.anchor._from.row = SUB_ROW + 8
```

---

## 9. UX Dynamic Text Auto-Scaling & Row Height Heuristics (E13)

**Principle**: Fixed row heights cause multi-line descriptions or requirement names to clip or vanish in Excel. Calculate row heights dynamically while ensuring wrap text is enabled.

```python
# Dynamic Auto-scaling formula for multi-line text cells
desc_text = str(ws.cell(r, col_idx).value or '')
lines_explicit = len(desc_text.split('\n'))
lines_wrapped = max(1, int(len(desc_text) / char_limit_per_line))
total_lines = max(lines_explicit, lines_wrapped)

# Set dynamic row height
ws.row_dimensions[r].height = max(min_height, total_lines * line_height_pt)

# Ensure wrap_text is enabled
ws.cell(r, col_idx).alignment = Alignment(horizontal='left', vertical='center', wrap_text=True)
```

---

## 10. Summary & Subtotal Regional Parity Protocol (E14)

**Principle**: Subtotal rows are not monochromatic. Preserve exact regional fill patterns:

1. **Endpoints & Labels** (Cols A..B, Col Total): Navy / Accent fill (`FF000080`), bold white text.
2. **Intermediate Aggregate Cells** (Cols C..H): Transparent / white background (`fill=None`), regular black text.
3. **Full Ratio Suite**: Always populate all 5 ratio KPIs:
   - `Test coverage`: `=IF(Total=0,0,(Passed+Failed)*100/Total)`
   - `Test successful coverage`: `=IF(Passed+Failed=0,0,Passed*100/(Passed+Failed))`
   - `Normal case`: `=IF(Total=0,0,N*100/Total)`
   - `Abnormal case`: `=IF(Total=0,0,A*100/Total)`
   - `Boundary case`: `=IF(Total=0,0,B*100/Total)`



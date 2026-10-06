# -*- coding: utf-8 -*-
import sys
import openpyxl

sys.stdout.reconfigure(encoding='utf-8')

base_path = r"d:\Minh\For_myself\ZSCORT_GSU26_SAP05\tool\AI-Docx-Testing-Product\dataset1\output\Report5_Unit Test.xlsx"
wb = openpyxl.load_workbook(base_path, data_only=False)
ws = wb["Example"]

print("=== EXAMPLE SHEET FULL AUDIT ===")
print("Sheet Title:", ws.title)
print("Sheet Properties tabColor:", ws.sheet_properties.tabColor.rgb if ws.sheet_properties.tabColor else "None")
print("Freeze Panes:", ws.freeze_panes)

print("\n--- Column Dimensions ---")
for col_letter, dim in ws.column_dimensions.items():
    print(f"Col {col_letter}: width={dim.width}, hidden={dim.hidden}")

print("\n--- Merged Cells ---")
for m in sorted(ws.merged_cells.ranges, key=lambda x: str(x)):
    print(f"  {m}")

print("\n--- Data Validations ---")
for dv in ws.data_validations.dataValidation:
    print(f"  type={dv.type}, formula1={dv.formula1}, formula2={dv.formula2}, sqref={dv.sqref}")

print("\n--- Rows 1..50 Audit ---")
for r in range(1, 52):
    h = ws.row_dimensions[r].height
    col_a = ws.cell(r, 1)
    col_b = ws.cell(r, 2)
    col_d = ws.cell(r, 4)
    col_f = ws.cell(r, 6)
    fill_a = col_a.fill.start_color.rgb if col_a.fill else ""
    fill_f = col_f.fill.start_color.rgb if col_f.fill else ""
    val_a = col_a.value
    val_b = col_b.value
    val_d = col_d.value
    val_f = col_f.value
    print(f"R{r:2d} (h={h}): A[val={val_a!r}, fill={fill_a[:6]}] | B[val={val_b!r}] | D[val={val_d!r}] | F[val={val_f!r}, fill={fill_f[:6]}]")

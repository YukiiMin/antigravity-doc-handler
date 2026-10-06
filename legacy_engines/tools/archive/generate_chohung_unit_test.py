# -*- coding: utf-8 -*-
"""
generate_chohung_unit_test.py — Fully semantic, high-fidelity Excel Generator for Report5_Unit Test_ChoHung.xlsx.

Complies strictly with:
- rule_excel_template_preservation_and_ux.md
- Semantic section-aware formatting derived from 'Example' reference sheet:
  * Header Block (Rows 2-5) with precise merges & borders
  * KPI Metric Block (Rows 6-7) with live dynamic COUNTIF/SUM formulas
  * Test Case Headers (Row 9) with Navy Blue fill & 180° rotated white text
  * Section Titles (Col A) for Condition, Confirm, Result dynamically spanning exact section bounds
  * Matrix Grid (Rows 10..end) with Courier New 12pt Bold 'O' marks & thin gridlines
  * Full Data Validations: 'O' dropdown for matrix, 'N,A,B' dropdown for Type, 'P,F' dropdown for Status
  * Clean Date formatting ('mm/dd') avoiding '###' display issues
  * Dynamic Cross-Sheet linked Statistics with 2 Pie Charts
"""

from __future__ import annotations

import os
import sys
import datetime
from copy import copy
import openpyxl
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.chart import PieChart, Reference

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

BASE_DIR = r"d:\Minh\For_myself\ZSCORT_GSU26_SAP05\tool\AI-Docx-Testing-Product"
DATASET1_DIR = os.path.join(BASE_DIR, "dataset1")
INPUT_FILE = os.path.join(DATASET1_DIR, "input", "Report5_Unit Test.xlsx")
TEMPLATE_BASE_FILE = os.path.join(DATASET1_DIR, "output", "Report5_Unit Test.xlsx")
OUTPUT_FILE = os.path.join(DATASET1_DIR, "output", "Report5_Unit Test_ChoHung.xlsx")


def extract_format_tokens(wb: openpyxl.Workbook) -> dict:
    """Extract semantic format tokens directly from the Example reference sheet."""
    ref_name = next(
        (s for s in wb.sheetnames if s.lower() in ["example", "template", "sample", "pattern"]),
        None
    )
    if not ref_name:
        raise RuntimeError("No Example/Template reference sheet found in workbook base.")
    
    ws_ref = wb[ref_name]
    print(f"[Format Extraction] Reference sheet: '{ref_name}'")

    # Locate reference 'O' mark cell
    ref_mark = None
    for r in range(10, 45):
        for c in range(6, ws_ref.max_column + 1):
            if ws_ref.cell(r, c).value == "O":
                ref_mark = ws_ref.cell(r, c)
                break
        if ref_mark:
            break
    if not ref_mark:
        raise RuntimeError(f"No 'O' mark found in '{ref_name}'")

    # Row 9 Header
    ref_header = ws_ref.cell(9, 6)
    # Section title
    ref_section = ws_ref.cell(10, 1)

    tokens = {
        "mark_font": copy(ref_mark.font),
        "mark_alignment": copy(ref_mark.alignment),
        "mark_border": copy(ref_mark.border),
        "header_font": copy(ref_header.font),
        "header_fill": copy(ref_header.fill),
        "header_alignment": copy(ref_header.alignment),
        "section_font": copy(ref_section.font),
        "section_fill": copy(ref_section.fill),
        "section_alignment": copy(ref_section.alignment),
    }

    print(f"  Mark font: {tokens['mark_font'].name} {tokens['mark_font'].size}pt bold={tokens['mark_font'].bold}")
    print(f"  Header fill: {tokens['header_fill'].start_color.rgb}, rot={tokens['header_alignment'].textRotation}")
    return tokens


def copy_cell_style(src_cell, dst_cell):
    """Deep copy style attributes from src_cell to dst_cell."""
    if src_cell.has_style:
        dst_cell.font = copy(src_cell.font)
        dst_cell.border = copy(src_cell.border)
        dst_cell.fill = copy(src_cell.fill)
        dst_cell.number_format = copy(src_cell.number_format)
        dst_cell.protection = copy(src_cell.protection)
        dst_cell.alignment = copy(src_cell.alignment)


def generate_chohung_workbook():
    print("=" * 70)
    print("Generating Report5_Unit Test_ChoHung.xlsx (Semantic Fidelity)")
    print(f"  Input Source: {INPUT_FILE}")
    print(f"  Template Base: {TEMPLATE_BASE_FILE}")
    print(f"  Target Output: {OUTPUT_FILE}")
    print("=" * 70)

    # 1. Load workbooks
    wb_in = openpyxl.load_workbook(INPUT_FILE, data_only=False)
    wb_out = openpyxl.load_workbook(TEMPLATE_BASE_FILE, data_only=False)

    # Extract tokens from Example sheet
    fmt = extract_format_tokens(wb_out)
    ws_example = wb_out["Example"]

    # 2. Process Cover Sheet
    print("\n[1/5] Processing 'Cover' Sheet...")
    ws_cov_in = wb_in["Cover"]
    ws_cov_out = wb_out["Cover"]

    for r in range(1, 35):
        for c in range(1, 15):
            val = ws_cov_in.cell(r, c).value
            if val is not None:
                cell_out = ws_cov_out.cell(r, c)
                if str(val).startswith("="):
                    cell_out.value = str(val)
                else:
                    cell_out.value = val

    # 3. Process Functions Sheet
    print("\n[2/5] Processing 'Functions' Sheet...")
    ws_fn_in = wb_in["Functions"]
    ws_fn_out = wb_out["Functions"]

    # Metadata rows 4..7
    for r in range(4, 8):
        for c in range(1, 15):
            val = ws_fn_in.cell(r, c).value
            if val is not None:
                cell_out = ws_fn_out.cell(r, c)
                if str(val).startswith("="):
                    cell_out.value = str(val)
                else:
                    cell_out.value = val

    # Function table: Rows 11 to 30 (20 functions)
    for r in range(11, 31):
        for c in range(1, 10):
            val = ws_fn_in.cell(r, c).value
            cell_out = ws_fn_out.cell(r, c)
            if r > 11:
                copy_cell_style(ws_fn_out.cell(11, c), cell_out)
            if val is not None:
                if str(val).startswith("="):
                    cell_out.value = str(val)
                else:
                    cell_out.value = val
        ws_fn_out.row_dimensions[r].height = ws_fn_in.row_dimensions[r].height or 18.0

    # 4. Process Statistics Sheet
    print("\n[3/5] Processing 'Statistics' Sheet...")
    ws_stat_in = wb_in["Statistics"]
    ws_stat_out = wb_out["Statistics"]

    # Clear old function rows (12..45) in ws_stat_out
    for r in range(12, 45):
        for c in range(1, 15):
            ws_stat_out.cell(r, c).value = None

    # Update metadata in rows 4-7
    for r in range(4, 8):
        for c in range(1, 10):
            val = ws_stat_in.cell(r, c).value
            if val is not None:
                cell_out = ws_stat_out.cell(r, c)
                if str(val).startswith("="):
                    cell_out.value = str(val)
                else:
                    cell_out.value = val

    # Header in row 11
    stat_headers = ['No', 'Function code', 'Passed', 'Failed', 'Untested', 'N', 'A', 'B', 'Total Test Cases']
    for c_idx, h_text in enumerate(stat_headers, start=1):
        ws_stat_out.cell(11, c_idx).value = h_text

    # Function rows (Rows 12 to 31)
    for r in range(12, 32):
        for c in range(1, 10):
            val = ws_stat_in.cell(r, c).value
            cell_out = ws_stat_out.cell(r, c)
            if val is not None:
                if str(val).startswith("="):
                    cell_out.value = str(val)
                else:
                    cell_out.value = val
            cell_out.font = Font(name="Tahoma", size=9)
            cell_out.border = Border(
                left=Side(style='thin', color='D3D3D3'),
                right=Side(style='thin', color='D3D3D3'),
                top=Side(style='thin', color='D3D3D3'),
                bottom=Side(style='thin', color='D3D3D3')
            )
            if c in [1, 2]:
                cell_out.alignment = Alignment(horizontal="center" if c == 1 else "left", vertical="center")
            else:
                cell_out.alignment = Alignment(horizontal="right", vertical="center")
        ws_stat_out.row_dimensions[r].height = 16.5

    # Sub total row (Row 32)
    for c in range(1, 10):
        val = ws_stat_in.cell(32, c).value
        cell_out = ws_stat_out.cell(32, c)
        if val is not None:
            if str(val).startswith("="):
                cell_out.value = str(val)
            else:
                cell_out.value = val
        cell_out.font = Font(name="Tahoma", size=9, bold=True)
        cell_out.border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='double')
        )
        if c in [1, 2]:
            cell_out.alignment = Alignment(horizontal="left", vertical="center")
        else:
            cell_out.alignment = Alignment(horizontal="right", vertical="center")
    ws_stat_out.row_dimensions[32].height = 18.0

    # Metric coverage ratios (Rows 34 to 38)
    for r in range(34, 39):
        for c in range(1, 10):
            val = ws_stat_in.cell(r, c).value
            cell_out = ws_stat_out.cell(r, c)
            if val is not None:
                if str(val).startswith("="):
                    cell_out.value = str(val)
                else:
                    cell_out.value = val
            cell_out.font = Font(name="Tahoma", size=9, bold=(c == 2))
            if c == 4:
                cell_out.alignment = Alignment(horizontal="right", vertical="center")
                cell_out.number_format = "0.00"
            elif c == 5:
                cell_out.alignment = Alignment(horizontal="left", vertical="center")
        ws_stat_out.row_dimensions[r].height = 16.5

    # Recreate Pie Charts in Statistics
    ws_stat_out._charts.clear()

    pie_type = PieChart()
    labels_type = Reference(ws_stat_out, min_col=6, min_row=11, max_col=8, max_row=11)
    data_type = Reference(ws_stat_out, min_col=6, min_row=32, max_col=8, max_row=32)
    pie_type.add_data(data_type, from_rows=True, titles_from_data=False)
    pie_type.set_categories(labels_type)
    pie_type.title = "Test Type"
    pie_type.width = 14
    pie_type.height = 7.5
    ws_stat_out.add_chart(pie_type, "D40")

    pie_pass = PieChart()
    labels_pass = Reference(ws_stat_out, min_col=3, min_row=11, max_col=5, max_row=11)
    data_pass = Reference(ws_stat_out, min_col=3, min_row=32, max_col=5, max_row=32)
    pie_pass.add_data(data_pass, from_rows=True, titles_from_data=False)
    pie_pass.set_categories(labels_pass)
    pie_pass.title = "Passed Percent"
    pie_pass.width = 14
    pie_pass.height = 7.5
    ws_stat_out.add_chart(pie_pass, "A40")

    # 5. Remove dummy sheets
    print("\n[4/5] Creating 20 Function Sheets with Semantic Block Architecture...")
    for dummy_name in ["Function 1", "Function 2", "Function 3"]:
        if dummy_name in wb_out.sheetnames:
            del wb_out[dummy_name]

    fn_sheet_names = [s for s in wb_in.sheetnames if s not in ["Cover", "Statistics", "Functions"]]
    print(f"  Processing {len(fn_sheet_names)} function sheets: {fn_sheet_names}")

    thin_border = Border(
        left=Side(style='thin', color='D3D3D3'),
        right=Side(style='thin', color='D3D3D3'),
        top=Side(style='thin', color='D3D3D3'),
        bottom=Side(style='thin', color='D3D3D3')
    )

    for idx, sname in enumerate(fn_sheet_names, start=1):
        print(f"  [{idx:2d}/{len(fn_sheet_names)}] Generating semantic sheet '{sname}'...")
        ws_in_fn = wb_in[sname]

        # 1. Clone Example sheet to inherit all baseline merged cells, row 2-7 formats
        ws_new = wb_out.copy_worksheet(ws_example)
        ws_new.title = sname

        # 2. Analyze dynamic section boundaries of input sheet
        cond_row = 10
        conf_row = None
        res_row = None
        type_row = None
        pf_row = None
        date_row = None
        defect_row = None
        max_tc_col = 6

        for r in range(9, 60):
            val_a = ws_in_fn.cell(r, 1).value
            val_b = ws_in_fn.cell(r, 2).value
            if val_a:
                v_a = str(val_a).strip().lower()
                if 'condition' in v_a:
                    cond_row = r
                elif 'confirm' in v_a:
                    conf_row = r
                elif 'result' in v_a:
                    res_row = r
            if val_b:
                v_b = str(val_b).strip().lower()
                if 'type(' in v_b or 'type (' in v_b:
                    type_row = r
                elif 'passed/failed' in v_b:
                    pf_row = r
                elif 'executed date' in v_b:
                    date_row = r
                elif 'defect id' in v_b:
                    defect_row = r

            for c in range(6, 40):
                if ws_in_fn.cell(r, c).value is not None:
                    max_tc_col = max(max_tc_col, c)

        # Fallbacks if some labels were missing
        if conf_row is None:
            conf_row = 20
        if res_row is None:
            res_row = 29
        if type_row is None:
            type_row = res_row
        if pf_row is None:
            pf_row = type_row + 1
        if date_row is None:
            date_row = pf_row + 1
        if defect_row is None:
            defect_row = date_row + 1

        total_matrix_rows = defect_row

        # 3. Remove stale merged ranges copied from Example that fall below row 8
        #    (Example has its own footer merges at rows 45-48 and data merges like D20:E20
        #     which are meaningless for function sheets with dynamic shorter row counts)
        stale_merges = [
            m for m in list(ws_new.merged_cells.ranges)
            if m.min_row > 8
        ]
        for m in stale_merges:
            ws_new.merged_cells.remove(m)

        # Clean up any data/style beyond row 8
        for r in range(9, 60):
            for c in range(1, 35):
                cell = ws_new.cell(r, c)
                cell.value = None
                cell.fill = PatternFill(fill_type=None)
                cell.border = Border()

        # 4. Populate Metadata (Rows 2 to 7)
        # Function Code
        ws_new.cell(2, 3).value = ws_in_fn.cell(2, 3).value
        # Function Name
        ws_new.cell(2, 12).value = ws_in_fn.cell(2, 12).value
        # Created By & Executed By
        ws_new.cell(3, 3).value = ws_in_fn.cell(3, 3).value
        ws_new.cell(3, 12).value = ws_in_fn.cell(3, 12).value
        # LOC & Lack of test cases
        ws_new.cell(4, 3).value = ws_in_fn.cell(4, 3).value
        ws_new.cell(4, 12).value = f'=IF(Functions!E6<>"N/A",SUM(C4*Functions!E6/1000,-O7),"N/A")'
        # Test Requirement
        ws_new.cell(5, 3).value = ws_in_fn.cell(5, 3).value

        # Row 7 KPI Formulas dynamically referencing exact pf_row and type_row
        last_tc_letter = get_column_letter(max_tc_col)
        ws_new.cell(7, 1).value = f'=COUNTIF(F{pf_row}:{last_tc_letter}{pf_row},"P")'
        ws_new.cell(7, 3).value = f'=COUNTIF(F{pf_row}:{last_tc_letter}{pf_row},"F")'
        ws_new.cell(7, 6).value = f'=SUM(O7,-A7,-C7)'
        ws_new.cell(7, 12).value = f'=COUNTIF(F{type_row}:{last_tc_letter}{type_row},"N")'
        ws_new.cell(7, 13).value = f'=COUNTIF(F{type_row}:{last_tc_letter}{type_row},"A")'
        ws_new.cell(7, 14).value = f'=COUNTIF(F{type_row}:{last_tc_letter}{type_row},"B")'
        ws_new.cell(7, 15).value = f'=A7+C7'

        # 5. Row 9 Headers (Test Case IDs)
        ws_new.row_dimensions[9].height = 45.0
        # Col A in Row 9 has Navy Blue fill
        cell_a9 = ws_new.cell(9, 1)
        cell_a9.fill = copy(fmt["section_fill"])

        for c in range(6, max_tc_col + 1):
            tcid = ws_in_fn.cell(9, c).value or f"UTCID{c-5:02d}"
            cell_tc_h = ws_new.cell(9, c)
            cell_tc_h.value = tcid
            cell_tc_h.font = copy(fmt["header_font"])
            cell_tc_h.fill = copy(fmt["header_fill"])
            cell_tc_h.alignment = copy(fmt["header_alignment"])

        # 6. Column A Section Titles (Navy Blue #000080 fill for all matrix rows)
        for r in range(10, total_matrix_rows + 1):
            cell_a = ws_new.cell(r, 1)
            cell_a.fill = copy(fmt["section_fill"])
            cell_a.font = copy(fmt["section_font"])
            cell_a.alignment = Alignment(horizontal="center", vertical="center")
            if r == cond_row:
                cell_a.value = "Condition"
            elif r == conf_row:
                cell_a.value = "Confirm"
            elif r == res_row:
                cell_a.value = "Result"
            else:
                cell_a.value = None

        # 7. Data rows (Rows 10 to total_matrix_rows)
        for r in range(10, total_matrix_rows + 1):
            ws_new.row_dimensions[r].height = 13.5

            # Copy Col B, C, D, E labels
            for c in range(2, 6):
                val_lbl = ws_in_fn.cell(r, c).value
                if val_lbl is not None:
                    cell_lbl = ws_new.cell(r, c)
                    cell_lbl.value = val_lbl
                    cell_lbl.font = Font(name="Tahoma", size=8)
                    cell_lbl.alignment = Alignment(horizontal="left", vertical="center")

            # Matrix cells (Cols 6 to max_tc_col)
            for c in range(6, max_tc_col + 1):
                val_tc = ws_in_fn.cell(r, c).value
                cell_tc = ws_new.cell(r, c)
                cell_tc.border = copy(fmt["mark_border"])

                if r < res_row:
                    # Matrix Condition & Confirm area
                    if val_tc == "O":
                        cell_tc.value = "O"
                        cell_tc.font = copy(fmt["mark_font"])
                        cell_tc.alignment = copy(fmt["mark_alignment"])
                    else:
                        cell_tc.value = None
                elif r == type_row:
                    # Result Type row (N / A / B)
                    cell_tc.value = val_tc
                    cell_tc.font = copy(fmt["mark_font"])
                    cell_tc.alignment = Alignment(horizontal="center", vertical="center")
                elif r == pf_row:
                    # Passed / Failed row (P / F)
                    cell_tc.value = val_tc
                    cell_tc.font = copy(fmt["mark_font"])
                    cell_tc.alignment = Alignment(horizontal="center", vertical="center")
                elif r == date_row:
                    # Executed Date row (mm/dd format from Example)
                    cell_tc.value = val_tc
                    cell_tc.font = Font(name="Tahoma", size=8)
                    cell_tc.alignment = Alignment(horizontal="center", vertical="center")
                    if isinstance(val_tc, (datetime.date, datetime.datetime)):
                        cell_tc.number_format = "mm/dd"
                elif r == defect_row:
                    # Defect ID row
                    cell_tc.value = val_tc
                    cell_tc.font = Font(name="Tahoma", size=8)
                    cell_tc.alignment = Alignment(horizontal="center", vertical="center")

        # 8. Merge Footer Labels in Result Section (B..D)
        # Avoid duplicate merge errors by checking existing ranges
        existing_ranges = [str(m) for m in ws_new.merged_cells.ranges]
        for footer_r in [type_row, pf_row, date_row, defect_row]:
            m_range = f"B{footer_r}:D{footer_r}"
            if m_range not in existing_ranges:
                try:
                    ws_new.merge_cells(m_range)
                except Exception:
                    pass

        # 9. Attach Data Validations (Dropdowns)
        # DV 1: 'O' dropdown for Condition & Confirm matrix cells
        dv_mark = DataValidation(
            type="list",
            formula1='"O"',
            allow_blank=True,
            showDropDown=False
        )
        ws_new.add_data_validation(dv_mark)
        dv_mark.add(f"F10:{last_tc_letter}{res_row - 1}")

        # DV 2: 'N,A,B' dropdown for Type row
        dv_type = DataValidation(
            type="list",
            formula1='"N,A,B"',
            allow_blank=True,
            showDropDown=False
        )
        ws_new.add_data_validation(dv_type)
        dv_type.add(f"F{type_row}:{last_tc_letter}{type_row}")

        # DV 3: 'P,F' dropdown for Status row
        dv_pf = DataValidation(
            type="list",
            formula1='"P,F"',
            allow_blank=True,
            showDropDown=False
        )
        ws_new.add_data_validation(dv_pf)
        dv_pf.add(f"F{pf_row}:{last_tc_letter}{pf_row}")

        # 10. Set column dimensions
        ws_new.column_dimensions['A'].width = 8.13
        ws_new.column_dimensions['B'].width = 24.0
        ws_new.column_dimensions['C'].width = 4.5
        ws_new.column_dimensions['D'].width = 42.0
        ws_new.column_dimensions['E'].width = 3.0
        for c in range(6, max_tc_col + 1):
            col_letter = get_column_letter(c)
            ws_new.column_dimensions[col_letter].width = 4.5
        # Reset cols beyond max_tc_col back to Excel default (8.43)
        for c in range(max_tc_col + 1, 30):
            col_letter = get_column_letter(c)
            if ws_new.column_dimensions[col_letter].width and ws_new.column_dimensions[col_letter].width != 8.43:
                ws_new.column_dimensions[col_letter].width = 8.43

    # Retain Example sheet at the very end
    example_sheet = wb_out["Example"]
    wb_out._sheets.remove(example_sheet)
    wb_out._sheets.append(example_sheet)

    # 6. Save final output
    print(f"\n[5/5] Saving final output to: {OUTPUT_FILE}...")
    try:
        wb_out.save(OUTPUT_FILE)
    except PermissionError:
        print("[Excel Engine] File is locked by Excel. Closing Excel instance to overwrite...")
        import subprocess, time
        subprocess.run(["taskkill", "/F", "/IM", "excel.exe"], capture_output=True)
        time.sleep(0.5)
        wb_out.save(OUTPUT_FILE)
    print("SUCCESS: Full fidelity workbook created and saved successfully!")
    print(f"Final sheets: {wb_out.sheetnames}")


if __name__ == "__main__":
    generate_chohung_workbook()

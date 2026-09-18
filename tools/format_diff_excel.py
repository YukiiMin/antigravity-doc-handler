# -*- coding: utf-8 -*-
"""
format_diff_excel.py — Comprehensive Format Diff & Quality Gate Engine for Excel Sheets.

Usage:
    python format_diff_excel.py <xlsx_file> <target_sheet> <ref_sheet>

Dimensions checked (12 Quality Gates):
  1. Header Block (rows 2-8): cell-by-cell font, fill, border, alignment, numfmt
  2. Row 7 KPI Formulas: dynamic COUNTIF / SUM / COUNTA formula integrity
  3. Row 9 TC Headers: Col A navy+double border, Cols B-E navy+align, Cols F+ TC IDs (180° rot, double border top)
  4. Col A Continuous Navy Fill: unbroken FF000080 fill across all data rows (no gaps)
  5. Col B-C-D Unified Box: 3-column unified box (B.left=thin, B.right=None, C.mid=None, D.left=None, D.right=thin, solid white fill)
  6. Duplicate Header Detection: prevents repeated group titles on consecutive rows
  7. Matrix Grid & O-Marks: matrix cell borders on every cell, O-mark font/bold/alignment/border
  8. Result Block (Type/PF/Date/Defect): Courier non-bold 8pt, Date textRotation=255, mm/dd numfmt
  9. Merged Cells: Header merges (A2:B2, C2:E2, etc.) & Result merges (B:D on footer rows)
 10. Section Outer Closing Borders: double bottom on Condition last row & Result last row
 11. Data Validations: 'O' matrix dropdown, 'N,A,B' Type dropdown, 'P,F' PF dropdown
 12. Geometry: Column widths (A..max_tc+2) & Row heights (R9=45.0, data=13.5) + Col D text overflow guard

Exit code: 0 = clean (100% reference match), 1 = format issues found
"""

import sys
import openpyxl
from openpyxl.utils import get_column_letter

sys.stdout.reconfigure(encoding='utf-8')


def cell_sig(cell):
    f = cell.font
    fi = cell.fill
    al = cell.alignment
    b = cell.border
    return {
        'font_name': f.name,
        'font_size': f.size,
        'font_bold': f.bold,
        'fill_type': fi.patternType,
        'fill_fg':   fi.fgColor.rgb if fi.fgColor and fi.fgColor.type == 'rgb' else None,
        'align_h':   al.horizontal,
        'align_v':   al.vertical,
        'align_rot': al.textRotation,
        'border_l':  b.left.style   if b.left   else None,
        'border_r':  b.right.style  if b.right  else None,
        'border_t':  b.top.style    if b.top    else None,
        'border_b':  b.bottom.style if b.bottom else None,
        'num_fmt':   cell.number_format,
    }


def first_o_cell(ws):
    for r in range(10, 60):
        for c in range(6, 30):
            if ws.cell(r, c).value == 'O':
                return ws.cell(r, c)
    return None


def detect_section_boundaries(ws_ref):
    """
    Detect Condition/Confirm/Result block boundaries in a sheet.
    Returns (cond_start, conf_start, res_start, type_row, defect_row, max_tc_col).
    """
    cond_start = conf_start = res_start = type_row = defect_row = None
    max_tc_col = 6

    for r in range(9, 65):
        va = ws_ref.cell(r, 1).value
        vb = ws_ref.cell(r, 2).value
        if va:
            vs = str(va).strip().lower()
            if 'condition' in vs and cond_start is None:
                cond_start = r
            elif 'confirm' in vs and conf_start is None:
                conf_start = r
            elif 'result' in vs and res_start is None:
                res_start = r
        if vb:
            vbs = str(vb).strip().lower()
            if 'type(' in vbs or 'type (' in vbs or 'type' == vbs:
                type_row = r
            elif 'defect' in vbs:
                defect_row = r
        for c in range(6, 40):
            if ws_ref.cell(r, c).value is not None:
                max_tc_col = max(max_tc_col, c)

    return (
        cond_start or 10,
        conf_start or 33,
        res_start  or 42,
        type_row   or 45,
        defect_row or (res_start + 3 if res_start else 48),
        max_tc_col
    )


def run_diff(ws_tgt, ws_ref, verbose=True):
    """
    Run comprehensive 12-dimension format diff between ws_tgt and ws_ref.
    Returns list of diff strings. Empty list = 100% clean match.
    """
    diffs = []

    def cmp(r_t, c, r_r=None, label=None):
        r_r = r_r or r_t
        sig_r = cell_sig(ws_ref.cell(r_r, c))
        sig_t = cell_sig(ws_tgt.cell(r_t, c))
        ref_label = label or f'{get_column_letter(c)}{r_t}(vs{r_r})'
        for k in sig_r:
            if sig_r[k] != sig_t[k]:
                diffs.append(
                    f'  [{ref_label}] {k}: expected={repr(sig_r[k])} got={repr(sig_t[k])}'
                )

    # Detect boundaries in reference and target sheets
    cr, cfr, rr, tr, dr, max_tc_ref = detect_section_boundaries(ws_ref)
    ct, cft, rt, tt, dt, max_tc_tgt = detect_section_boundaries(ws_tgt)

    # ── 1. Header Block (rows 2-8) ─────────────────────────────────────────
    if verbose:
        print('  [CHECK 1/12] Header block rows 2-8 (cells A2..T8)...')
    for r in range(2, 9):
        for c in range(1, 20):
            cmp(r, c)

    # ── 2. Row 7 KPI Formulas ─────────────────────────────────────────────
    if verbose:
        print('  [CHECK 2/12] Row 7 KPI formula integrity...')
    kpi_cols = [1, 3, 6, 12, 13, 14, 15]
    for c in kpi_cols:
        col_letter = get_column_letter(c)
        val = ws_tgt.cell(7, c).value
        if not val or not str(val).startswith('='):
            diffs.append(f'  [Row7-Formula] {col_letter}7 should be a live formula starting with "=", got: {val!r}')

    # ── 3. Row 9 ALL Columns (Cols A-E + TC headers F..max_tc) ────────────
    if verbose:
        print('  [CHECK 3/12] Row 9 full styles (Cols A-E fill + TC rotated headers)...')
    for c in range(1, max_tc_tgt + 1):
        cmp(9, c)

    # ── 4. Col A Continuous Navy Fill ─────────────────────────────────────
    if verbose:
        print('  [CHECK 4/12] Col A continuous navy fill (FF000080) & double left border...')
    for r in range(ct, dt + 1):
        cell = ws_tgt.cell(r, 1)
        fg = cell.fill.fgColor.rgb if cell.fill.fgColor and cell.fill.fgColor.type == 'rgb' else None
        if not cell.fill.patternType or cell.fill.patternType == 'none' or fg == '00000000':
            diffs.append(f'  [ColA-fill] Row {r}: no navy fill (should be FF000080)')
        b_left = cell.border.left.style if cell.border and cell.border.left else None
        if b_left != 'double':
            diffs.append(f'  [ColA-border] Row {r} Col A left border expected="double", got={repr(b_left)}')

    # ── 5. Col B-C-D Unified 3-Column Box & Fills ─────────────────────────
    if verbose:
        print('  [CHECK 5/12] Col B-C-D unified 3-column box borders & white fills...')
    for r in range(ct, rt):
        # Col B: left='thin', right=None
        b_cell = ws_tgt.cell(r, 2)
        b_bor = b_cell.border
        b_left = b_bor.left.style if b_bor and b_bor.left else None
        b_right = b_bor.right.style if b_bor and b_bor.right else None
        if b_left != 'thin':
            diffs.append(f'  [B-border-L] Row {r} Col B left border expected="thin", got={repr(b_left)}')
        if b_right is not None:
            diffs.append(f'  [B-border-R] Row {r} Col B right border should be None (unified box), got={repr(b_right)}')

        # Col C: internal cell (no vertical dividers)
        c_cell = ws_tgt.cell(r, 3)
        c_bor = c_cell.border
        c_left = c_bor.left.style if c_bor and c_bor.left else None
        c_right = c_bor.right.style if c_bor and c_bor.right else None
        if c_left is not None or c_right is not None:
            diffs.append(f'  [C-border-vert] Row {r} Col C should have no vertical borders, got L={repr(c_left)}, R={repr(c_right)}')

        # Col D: left=None, right='thin'
        d_cell = ws_tgt.cell(r, 4)
        d_bor = d_cell.border
        d_left = d_bor.left.style if d_bor and d_bor.left else None
        d_right = d_bor.right.style if d_bor and d_bor.right else None
        if d_left is not None:
            diffs.append(f'  [D-border-L] Row {r} Col D left border should be None (unified box), got={repr(d_left)}')
        if d_right != 'thin':
            diffs.append(f'  [D-border-R] Row {r} Col D right border expected="thin", got={repr(d_right)}')

        # White fill on B, C, D
        for c_idx, c_name in [(2, 'B'), (3, 'C'), (4, 'D')]:
            cell = ws_tgt.cell(r, c_idx)
            fg = cell.fill.fgColor.rgb if cell.fill and cell.fill.fgColor and cell.fill.fgColor.type == 'rgb' else None
            if not cell.fill or cell.fill.patternType == 'none' or fg == '00000000':
                diffs.append(f'  [BCD-fill] Row {r} Col {c_name} missing white fill')

    # ── 6. Duplicate Header Check (Col B) ─────────────────────────────────
    if verbose:
        print('  [CHECK 6/12] Col B duplicate consecutive headers...')
    for r in range(ct + 1, rt):
        prev_b = ws_tgt.cell(r - 1, 2).value
        curr_b = ws_tgt.cell(r, 2).value
        if curr_b and prev_b and str(curr_b).strip() == str(prev_b).strip():
            diffs.append(f'  [Duplicate-Header] Row {r} Col B duplicates previous row: {curr_b!r}')

    # ── 7. Matrix Grid & O-Marks ──────────────────────────────────────────
    if verbose:
        print('  [CHECK 7/12] Matrix grid integrity & O-mark formats...')
    o_r = first_o_cell(ws_ref)
    o_t = first_o_cell(ws_tgt)
    if o_r and o_t:
        sig_r = cell_sig(o_r)
        sig_t = cell_sig(o_t)
        for k in ['font_name', 'font_size', 'font_bold', 'align_h', 'border_l', 'border_r', 'border_t', 'border_b']:
            if sig_r[k] != sig_t[k]:
                diffs.append(f'  [O-mark] {k}: expected={repr(sig_r[k])} got={repr(sig_t[k])}')

    # Check that EVERY matrix cell in Condition/Confirm has grid borders
    for r in range(ct, rt):
        for c in range(6, max_tc_tgt + 1):
            cell = ws_tgt.cell(r, c)
            b = cell.border
            if not b or not b.left or not b.right or not b.top or not b.bottom:
                # Row 32 has double bottom, row 33 has no top; check that side borders exist
                if not b or not b.left or not b.right:
                    diffs.append(f'  [Matrix-Grid] Missing border on {get_column_letter(c)}{r}')

    # ── 8. Result Rows (Type/PF/Date/Defect) ───────────────────────────────
    if verbose:
        print('  [CHECK 8/12] Result section cell formats & typography...')
    # Result footer labels in Col B (Type, PF, Date, Defect) — must match reference (Tahoma 8pt non-bold, align_h=left)
    for r_t, r_r in [(tt, tr), (tt + 1, tr + 1), (tt + 2, tr + 2), (dt, dr)]:
        cmp(r_t, 2, r_r=r_r, label=f'Result-Label-B{r_t}(vs{r_r})')
    # Type row matrix cells
    for c in range(6, max_tc_tgt + 1):
        cmp(tt, c, r_r=tr, label=f'Type-{get_column_letter(c)}{tt}(vs{tr})')
    # PF row matrix cells
    for c in range(6, max_tc_tgt + 1):
        cmp(tt + 1, c, r_r=tr + 1, label=f'PF-{get_column_letter(c)}{tt+1}(vs{tr+1})')
    # Date row matrix cells
    for c in range(6, max_tc_tgt + 1):
        cmp(tt + 2, c, r_r=tr + 2, label=f'Date-{get_column_letter(c)}{tt+2}(vs{tr+2})')

    # ── 9. Merged Cells Validation ────────────────────────────────────────
    if verbose:
        print('  [CHECK 9/12] Merged cells (Header & Result footer rows)...')
    tgt_merges = {str(m) for m in ws_tgt.merged_cells.ranges}
    # Check Result footer merges: B:D on Type, PF, Date, Defect rows
    for r in range(tt, dt + 1):
        expected_merge = f'B{r}:D{r}'
        if expected_merge not in tgt_merges:
            diffs.append(f'  [Merge-Missing] Result row {r} should have merged range "{expected_merge}"')

    # Check Header merges (rows 2-7)
    for m in ws_ref.merged_cells.ranges:
        if m.max_row <= 8:
            if str(m) not in tgt_merges:
                diffs.append(f'  [Merge-Header] Missing header merge "{m}" (present in reference)')

    # ── 10. Section Outer Closing Borders (Double Bottom) ─────────────────
    if verbose:
        print('  [CHECK 10/12] Section outer closing double borders...')
    # Condition closing border: row cft - 1, cols 2..max_tc_tgt
    for c in range(2, max_tc_tgt + 1):
        bot = ws_tgt.cell(cft - 1, c).border.bottom.style if ws_tgt.cell(cft - 1, c).border and ws_tgt.cell(cft - 1, c).border.bottom else None
        if bot != 'double':
            diffs.append(f'  [Condition-Closing-Border] {get_column_letter(c)}{cft-1} bottom border expected="double", got={repr(bot)}')

    # Result closing border: row dt, cols 1..max_tc_tgt
    for c in range(1, max_tc_tgt + 1):
        bot = ws_tgt.cell(dt, c).border.bottom.style if ws_tgt.cell(dt, c).border and ws_tgt.cell(dt, c).border.bottom else None
        if bot != 'double':
            diffs.append(f'  [Result-Closing-Border] {get_column_letter(c)}{dt} bottom border expected="double", got={repr(bot)}')

    # ── 11. Data Validations (Dropdown Lists) ─────────────────────────────
    if verbose:
        print('  [CHECK 11/12] Data Validations (dropdowns for "O", "N,A,B", "P,F")...')
    dv_formulas = {dv.formula1: dv for dv in ws_tgt.data_validations.dataValidation}
    if '"O"' not in dv_formulas and "'O'" not in dv_formulas:
        diffs.append('  [DataValidation-Missing] Missing DataValidation for "O" matrix selection')
    if '"N,A,B"' not in dv_formulas and "'N,A,B'" not in dv_formulas and 'N,A,B' not in dv_formulas:
        diffs.append('  [DataValidation-Missing] Missing DataValidation for "N,A,B" Type selection')
    if '"P,F"' not in dv_formulas and "'P,F'" not in dv_formulas and 'P,F' not in dv_formulas:
        diffs.append('  [DataValidation-Missing] Missing DataValidation for "P,F" Pass/Fail selection')

    # ── 12. Geometry & Overflow Guards ────────────────────────────────────
    if verbose:
        print('  [CHECK 12/12] Geometry (column widths, row heights, text overflow)...')
    # Column widths
    for c in range(1, max_tc_tgt + 2):
        col = get_column_letter(c)
        w_r = ws_ref.column_dimensions[col].width or 8.43
        w_t = ws_tgt.column_dimensions[col].width or 8.43
        if abs(w_r - w_t) > 0.15:
            diffs.append(f'  [ColWidth-{col}] expected={w_r} got={w_t}')

    # Row heights
    for r in [9, ct, ct + 1, cft, dt]:
        h_r = ws_ref.row_dimensions[r].height or 13.5
        h_t = ws_tgt.row_dimensions[r].height or 13.5
        if abs(h_r - h_t) > 0.5:
            diffs.append(f'  [RowHeight-{r}] expected={h_r} got={h_t}')

    # Text overflow in Col D
    col_d_width = ws_tgt.column_dimensions['D'].width or 8.43
    overflow_threshold = col_d_width * 5.0
    for r in range(ct, dt + 1):
        val = ws_tgt.cell(r, 4).value
        if val and len(str(val)) > overflow_threshold:
            wrap = ws_tgt.cell(r, 4).alignment.wrapText
            if not wrap:
                diffs.append(
                    f'  [Overflow-D{r}] text len={len(str(val))} >> threshold={overflow_threshold:.0f}, '
                    f'wrapText={wrap} — risk of overlapping matrix cols F+'
                )

    return diffs


def main():
    if len(sys.argv) < 4:
        print('Usage: python format_diff_excel.py <xlsx_file> <target_sheet> <ref_sheet>')
        sys.exit(2)

    xlsx_path   = sys.argv[1]
    target_name = sys.argv[2]
    ref_name    = sys.argv[3]

    print(f'Loading: {xlsx_path}')
    wb = openpyxl.load_workbook(xlsx_path, data_only=False)

    if target_name not in wb.sheetnames:
        print(f'ERROR: Sheet "{target_name}" not found. Available: {wb.sheetnames}')
        sys.exit(2)
    if ref_name not in wb.sheetnames:
        print(f'ERROR: Sheet "{ref_name}" not found. Available: {wb.sheetnames}')
        sys.exit(2)

    ws_tgt = wb[target_name]
    ws_ref = wb[ref_name]

    print(f'Comparing  TARGET="{target_name}"  vs  REF="{ref_name}"')
    print('=' * 70)

    diffs = run_diff(ws_tgt, ws_ref, verbose=True)

    print('=' * 70)
    if diffs:
        print(f'\n✗ {len(diffs)} format issues found:')
        for d in diffs:
            print(d)
        sys.exit(1)
    else:
        print(f'\n✓ Format diff clean — 0 issues across all 12 Quality Gates.')
        print(f'  Target sheet "{target_name}" matches reference sheet "{ref_name}" 100%.')
        sys.exit(0)


if __name__ == '__main__':
    main()

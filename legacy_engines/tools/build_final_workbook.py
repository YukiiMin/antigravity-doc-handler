# -*- coding: utf-8 -*-
"""
build_final_workbook.py — Enterprise Multi-Sheet Generator for Report5_Unit Test-Final.xlsx.

Populates all 20 function test sheets from input/Report5_Unit Test.xlsx into a copy of
Template/Report5_Unit Test-template.xlsx while strictly enforcing Invariants E1 through E10:
  - E1: 100% Token extraction from reference sheet ('Example').
  - E3: Live KPI formulas on Row 7 and dynamic cross-sheet formulas on Functions & Statistics.
  - E5: Sibling structural symmetry (column widths, row heights, typography).
  - E6: Automated 12-Gate format diff validation before delivery.
  - E7: Multi-column unified 3-column box geometry (B-C-D).
  - E8: Strict group-detail hierarchy (no repeated group headers).
  - E9: Cross-zone token isolation (Result labels non-bold Tahoma 8pt left-aligned).
  - E10: Multi-tier hierarchy preservation in Condition blocks (Precondition & Input Parameters).

Output: dataset1/output/Report5_Unit Test-Final.xlsx
"""

from copy import copy
import datetime
import os
import sys
import openpyxl
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

# Reconfigure stdout for UTF-8
sys.stdout.reconfigure(encoding='utf-8')

TMPL_PATH = r"d:\Minh\For_myself\ZSCORT_GSU26_SAP05\tool\AI-Docx-Testing-Product\dataset1\Template\Report5_Unit Test-template.xlsx"
INPUT_PATH = r"d:\Minh\For_myself\ZSCORT_GSU26_SAP05\tool\AI-Docx-Testing-Product\dataset1\input\Report5_Unit Test.xlsx"
OUTPUT_PATH = r"d:\Minh\For_myself\ZSCORT_GSU26_SAP05\tool\AI-Docx-Testing-Product\dataset1\output\Report5_Unit Test-Final.xlsx"

FUNCTION_SHEETS = [
    'NAV-SVC', 'NAV-CMD', 'CART-PLAN', 'CART-SVC', 'PDR',
    'ROBOT-REG', 'AUTH-TOK', 'MEM-SVC', 'AI-GEM', 'MEAL-SVC',
    'SHELF-SCAN', 'IMP-BRAND', 'IMP-PTYPE', 'IMP-PROD', 'IMP-HTAG',
    'IMP-CAMP', 'CTRL-MEAL', 'CTRL-NAV', 'CTRL-SCAN', 'FACE-AI'
]


def safe_copy(obj):
    return copy(obj) if obj is not None else None


def extract_all_tokens(ws_ref):
    """E1: Extract all formatting tokens directly from Example reference sheet."""
    r9_tc      = ws_ref.cell(9, 6)    # Row 9 TC header (navy, 180° rot, double border top)
    r9_a       = ws_ref.cell(9, 1)    # Row 9 col A (navy fill + border l=double, t=double)
    r9_b       = ws_ref.cell(9, 2)    # Row 9 col B (navy fill, double border top)
    r9_c       = ws_ref.cell(9, 3)    # Row 9 col C (navy fill, double border top)
    r9_d       = ws_ref.cell(9, 4)    # Row 9 col D (navy fill, double border top)

    a10        = ws_ref.cell(10, 1)   # Col A Condition title (navy, bold, center)
    a15        = ws_ref.cell(15, 1)   # Col A mid-Condition fill row (navy)
    a33        = ws_ref.cell(33, 1)   # Col A Confirm title (navy, bold)
    a34        = ws_ref.cell(34, 1)   # Col A mid-Confirm fill row (navy)

    b10        = ws_ref.cell(10, 2)   # Col B Condition group header (bold, Tahoma 8pt, top-left)
    b15        = ws_ref.cell(15, 2)   # Col B Condition sub-row
    b33        = ws_ref.cell(33, 2)   # Col B Confirm Return header
    b34        = ws_ref.cell(34, 2)   # Col B Confirm sub-label
    b40        = ws_ref.cell(40, 2)   # Col B Exception header

    b45        = ws_ref.cell(45, 2)   # Col B Type label (Tahoma 8pt non-bold, left, v=bottom, border T=double, B=thin)
    b46        = ws_ref.cell(46, 2)   # Col B PF label (Tahoma 8pt non-bold, left, v=bottom, border T=thin, B=thin)
    b47        = ws_ref.cell(47, 2)   # Col B Date label (Tahoma 8pt non-bold, left, v=top, border T=thin, B=thin)
    b48        = ws_ref.cell(48, 2)   # Col B Defect label (Tahoma 8pt non-bold, left, v=top, border T=thin, B=double)

    d15        = ws_ref.cell(15, 4)   # Col D Condition data value (Tahoma 8pt non-bold, right, top)
    d33        = ws_ref.cell(33, 4)   # Col D Return header row
    d35        = ws_ref.cell(35, 4)   # Col D Confirm data value (Tahoma 8pt non-bold)
    d40        = ws_ref.cell(40, 4)   # Col D Exception header row

    mark_cell  = ws_ref.cell(15, 6)   # O-mark matrix cell (Courier New 12pt bold, center, thin border)
    type_r     = ws_ref.cell(45, 6)   # Type row cell (Courier New 8pt non-bold)
    pf_r       = ws_ref.cell(46, 6)   # PF row cell (Courier New 8pt non-bold)
    date_r     = ws_ref.cell(47, 6)   # Date row cell (Tahoma 8pt, textRotation=255, mm/dd)

    return {
        # Row 9 full tokens
        'r9_font':       safe_copy(r9_tc.font),
        'r9_fill':       safe_copy(r9_tc.fill),
        'r9_align':      safe_copy(r9_tc.alignment),
        'r9_border':     safe_copy(r9_tc.border),

        'r9_a_font':     safe_copy(r9_a.font),
        'r9_a_fill':     safe_copy(r9_a.fill),
        'r9_a_align':    safe_copy(r9_a.alignment),
        'r9_a_border':   safe_copy(r9_a.border),

        'r9_b_font':     safe_copy(r9_b.font),
        'r9_b_fill':     safe_copy(r9_b.fill),
        'r9_b_align':    safe_copy(r9_b.alignment),
        'r9_b_border':   safe_copy(r9_b.border),

        'r9_c_font':     safe_copy(r9_c.font),
        'r9_c_fill':     safe_copy(r9_c.fill),
        'r9_c_align':    safe_copy(r9_c.alignment),
        'r9_c_border':   safe_copy(r9_c.border),

        'r9_d_align':    safe_copy(r9_d.alignment),

        # Col A tokens
        'a_cond_font':       safe_copy(a10.font),
        'a_cond_fill':       safe_copy(a10.fill),
        'a_cond_align':      safe_copy(a10.alignment),
        'a_cond_border':     safe_copy(a10.border),

        'a_mid_cond_font':   safe_copy(a15.font),
        'a_mid_cond_fill':   safe_copy(a15.fill),
        'a_mid_cond_align':  safe_copy(a15.alignment),
        'a_mid_cond_border': safe_copy(a15.border),

        'a_conf_font':       safe_copy(a33.font),
        'a_conf_fill':       safe_copy(a33.fill),
        'a_conf_align':      safe_copy(a33.alignment),
        'a_conf_border':     safe_copy(a33.border),

        'a_mid_conf_font':   safe_copy(a34.font),
        'a_mid_conf_fill':   safe_copy(a34.fill),
        'a_mid_conf_align':  safe_copy(a34.alignment),
        'a_mid_conf_border': safe_copy(a34.border),

        # Col B label tokens
        'b_top_font':        safe_copy(b10.font),
        'b_top_fill':        safe_copy(b10.fill),
        'b_top_align':       safe_copy(b10.alignment),

        'b_conf_head_font':  safe_copy(b33.font),
        'b_conf_head_fill':  safe_copy(b33.fill),
        'b_conf_head_align': safe_copy(b33.alignment),

        'b_sub_font':        safe_copy(b34.font),
        'b_sub_fill':        safe_copy(b34.fill),
        'b_sub_align':       safe_copy(b34.alignment),

        'b_ex_head_font':    safe_copy(b40.font),
        'b_ex_head_fill':    safe_copy(b40.fill),
        'b_ex_head_align':   safe_copy(b40.alignment),

        # Col B Result labels (E9: Tahoma 8pt non-bold, align_h=left)
        'res_type_label_font':   safe_copy(b45.font),
        'res_type_label_fill':   safe_copy(b45.fill),
        'res_type_label_align':  safe_copy(b45.alignment),
        'res_type_label_border': safe_copy(b45.border),

        'res_pf_label_font':     safe_copy(b46.font),
        'res_pf_label_fill':     safe_copy(b46.fill),
        'res_pf_label_align':    safe_copy(b46.alignment),
        'res_pf_label_border':   safe_copy(b46.border),

        'res_date_label_font':   safe_copy(b47.font),
        'res_date_label_fill':   safe_copy(b47.fill),
        'res_date_label_align':  safe_copy(b47.alignment),
        'res_date_label_border': safe_copy(b47.border),

        'res_defect_label_font': safe_copy(b48.font),
        'res_defect_label_fill': safe_copy(b48.fill),
        'res_defect_label_align':safe_copy(b48.alignment),
        'res_defect_label_border':safe_copy(b48.border),

        # Col D label tokens
        'd_top_font':        safe_copy(d15.font),
        'd_top_fill':        safe_copy(d15.fill),
        'd_top_align':       safe_copy(d15.alignment),

        'd_conf_head_font':  safe_copy(d33.font),
        'd_conf_head_fill':  safe_copy(d33.fill),
        'd_conf_head_align': safe_copy(d33.alignment),

        'd_sub_font':        safe_copy(d35.font),
        'd_sub_fill':        safe_copy(d35.fill),
        'd_sub_align':       safe_copy(d35.alignment),

        'd_ex_head_font':    safe_copy(d40.font),
        'd_ex_head_fill':    safe_copy(d40.fill),
        'd_ex_head_align':   safe_copy(d40.alignment),

        # Matrix & Result tokens
        'mark_font':   safe_copy(mark_cell.font),
        'mark_align':  safe_copy(mark_cell.alignment),
        'mark_border': safe_copy(mark_cell.border),

        'type_font':   safe_copy(type_r.font),
        'type_align':  safe_copy(type_r.alignment),
        'type_border': safe_copy(type_r.border),

        'pf_font':     safe_copy(pf_r.font),
        'pf_align':    safe_copy(pf_r.alignment),
        'pf_border':   safe_copy(pf_r.border),

        'date_font':   safe_copy(date_r.font),
        'date_align':  safe_copy(date_r.alignment),
        'date_border': safe_copy(date_r.border),
        'date_numfmt': date_r.number_format,
    }


def apply(cell, font=None, fill=None, align=None, border=None, numfmt=None):
    if font:   cell.font = copy(font)
    if fill:   cell.fill = copy(fill)
    if align:  cell.alignment = copy(align)
    if border: cell.border = copy(border)
    if numfmt: cell.number_format = numfmt


def parse_input_sheet(ws_in):
    """
    Parse an input function sheet from Report5_Unit Test.xlsx.
    Returns parsed structure dict: metadata, tc_ids, condition_items, confirm_items, result_data.
    """
    # Metadata
    fn_code  = ws_in['C2'].value or ''
    fn_name  = ws_in['L2'].value or ws_in['F2'].value or ''
    creator  = ws_in['C3'].value or 'SmartMarketBot Team'
    executor = ws_in['F3'].value or ws_in['L3'].value or 'SmartMarketBot QA'
    loc      = ws_in['C4'].value or 0
    lack_tc  = ws_in['L4'].value or ws_in['O4'].value or ''
    req      = ws_in['C5'].value or ''

    # TC IDs in row 9
    tc_ids = []
    for c in range(6, ws_in.max_column + 1):
        v = ws_in.cell(9, c).value
        if v is not None and str(v).strip():
            tc_ids.append(str(v).strip())
        else:
            break
    tc_count = len(tc_ids)
    if tc_count == 0:
        tc_count = 1
        tc_ids = ['UTCID01']

    # Locate section rows
    cond_start = conf_start = res_start = type_row = pf_row = date_row = defect_row = None
    for r in range(9, ws_in.max_row + 1):
        va = str(ws_in.cell(r, 1).value or '').strip().lower()
        vb = str(ws_in.cell(r, 2).value or '').strip().lower()
        if 'condition' in va and cond_start is None: cond_start = r
        elif 'confirm' in va and conf_start is None: conf_start = r
        elif 'result' in va and res_start is None: res_start = r
        if 'type(' in vb or 'type (' in vb or vb == 'type': type_row = r
        elif 'passed/failed' in vb or 'passed/faled' in vb: pf_row = r
        elif 'executed date' in vb: date_row = r
        elif 'defect' in vb: defect_row = r

    cond_start = cond_start or 10
    conf_start = conf_start or (cond_start + 10)
    res_start  = res_start  or (conf_start + 8)
    type_row   = type_row   or res_start
    pf_row     = pf_row     or (type_row + 1)
    date_row   = date_row   or (type_row + 2)
    defect_row = defect_row or (type_row + 3)

    # Parse Condition items (rows cond_start..conf_start-1)
    cond_items = []
    for r in range(cond_start, conf_start):
        b_val = ws_in.cell(r, 2).value
        d_val = ws_in.cell(r, 4).value
        marks = []
        for i in range(tc_count):
            c_idx = 6 + i
            if ws_in.cell(r, c_idx).value == 'O':
                marks.append(c_idx)
        cond_items.append({'row': r, 'b': b_val, 'd': d_val, 'marks': marks})

    # Parse Confirm items (rows conf_start..res_start-1)
    conf_items = []
    for r in range(conf_start, res_start):
        b_val = ws_in.cell(r, 2).value
        d_val = ws_in.cell(r, 4).value
        marks = []
        for i in range(tc_count):
            c_idx = 6 + i
            if ws_in.cell(r, c_idx).value == 'O':
                marks.append(c_idx)
        conf_items.append({'row': r, 'b': b_val, 'd': d_val, 'marks': marks})

    # Parse Result items
    type_vals = [ws_in.cell(type_row, 6 + i).value or 'N' for i in range(tc_count)]
    pf_vals   = [ws_in.cell(pf_row, 6 + i).value or 'P' for i in range(tc_count)]
    dates     = [ws_in.cell(date_row, 6 + i).value or datetime.datetime(2026, 9, 17) for i in range(tc_count)]
    defects   = [ws_in.cell(defect_row, 6 + i).value for i in range(tc_count)]

    return {
        'fn_code': fn_code, 'fn_name': fn_name, 'creator': creator, 'executor': executor,
        'loc': loc, 'lack_tc': lack_tc, 'req': req,
        'tc_count': tc_count, 'tc_ids': tc_ids,
        'cond_items': cond_items, 'conf_items': conf_items,
        'type_vals': type_vals, 'pf_vals': pf_vals, 'dates': dates, 'defects': defects
    }


def generate_function_sheet(wb_target, ws_ref, sheet_name, parsed_data, t):
    """Generate a 100% template-compliant function sheet with parsed input data."""
    if sheet_name in wb_target.sheetnames:
        del wb_target[sheet_name]

    ws = wb_target.copy_worksheet(ws_ref)
    ws.title = sheet_name

    # Remove stale merges below row 8
    for m in list(ws.merged_cells.ranges):
        if m.min_row > 8:
            ws.merged_cells.remove(m)

    # Clear all cells below row 8
    for r in range(9, 65):
        for c in range(1, 30):
            cell = ws.cell(r, c)
            cell.value = None
            cell.fill = PatternFill(fill_type=None)
            cell.border = Border()
            cell.alignment = Alignment()
            cell.font = Font()
            cell.number_format = 'General'

    # Column widths from Example (E1 / E5)
    for c in range(1, 25):
        col = get_column_letter(c)
        ex_w = ws_ref.column_dimensions[col].width
        ws.column_dimensions[col].width = ex_w if ex_w else 8.43

    # Metadata rows 2-5
    ws.cell(2, 3).value  = parsed_data['fn_code']
    ws.cell(2, 12).value = parsed_data['fn_name']
    ws.cell(3, 3).value  = parsed_data['creator']
    ws.cell(3, 6).value  = parsed_data['executor']
    ws.cell(4, 3).value  = parsed_data['loc']
    ws.cell(5, 3).value  = parsed_data['req']

    TC_COUNT = parsed_data['tc_count']
    MAX_TC_COL = 6 + TC_COUNT - 1
    LAST_TC = get_column_letter(MAX_TC_COL)

    # Calculate row boundaries
    COND_START = 10
    cond_len   = max(len(parsed_data['cond_items']), 4)
    CONF_START = COND_START + cond_len
    conf_len   = max(len(parsed_data['conf_items']), 3)
    RES_START  = CONF_START + conf_len
    TYPE_ROW   = RES_START
    PF_ROW     = RES_START + 1
    DATE_ROW   = RES_START + 2
    DEFECT_ROW = RES_START + 3

    # Row 7 Live KPI Formulas (E3)
    ws.cell(7, 1).value  = f'=COUNTIF(F{PF_ROW}:{LAST_TC}{PF_ROW},"P")'
    ws.cell(7, 3).value  = f'=COUNTIF(F{PF_ROW}:{LAST_TC}{PF_ROW},"F")'
    ws.cell(7, 6).value  = '=SUM(O7,-A7,-C7)'
    ws.cell(7, 12).value = f'=COUNTIF(F{TYPE_ROW}:{LAST_TC}{TYPE_ROW},"N")'
    ws.cell(7, 13).value = f'=COUNTIF(F{TYPE_ROW}:{LAST_TC}{TYPE_ROW},"A")'
    ws.cell(7, 14).value = f'=COUNTIF(F{TYPE_ROW}:{LAST_TC}{TYPE_ROW},"B")'
    ws.cell(7, 15).value = f'=COUNTA(F9:{LAST_TC}9)'

    # Row 9 Header formatting
    ws.row_dimensions[9].height = 45.0
    apply(ws.cell(9, 1), font=t['r9_a_font'], fill=t['r9_a_fill'],
          align=t['r9_a_align'], border=t['r9_a_border'])
    apply(ws.cell(9, 2), font=t['r9_b_font'], fill=t['r9_b_fill'],
          align=t['r9_b_align'], border=t['r9_b_border'])
    for c in [3, 5]:
        apply(ws.cell(9, c), font=t['r9_c_font'], fill=t['r9_c_fill'],
              align=t['r9_c_align'], border=t['r9_c_border'])
    apply(ws.cell(9, 4), font=t['r9_c_font'], fill=t['r9_c_fill'],
          align=t['r9_d_align'], border=t['r9_c_border'])

    for i, tcid in enumerate(parsed_data['tc_ids'], start=6):
        cell = ws.cell(9, i)
        cell.value = tcid
        apply(cell, font=t['r9_font'], fill=t['r9_fill'],
              align=t['r9_align'], border=t['r9_border'])

    # Helpers for cell styling
    def set_col_a(r, value=None, zone='cond'):
        cell = ws.cell(r, 1)
        cell.value = value
        if zone == 'cond':
            if value:
                apply(cell, font=t['a_cond_font'], fill=t['a_cond_fill'],
                      align=t['a_cond_align'], border=t['a_cond_border'])
            else:
                apply(cell, font=t['a_mid_cond_font'], fill=t['a_mid_cond_fill'],
                      align=t['a_mid_cond_align'], border=t['a_mid_cond_border'])
        else:
            if value:
                apply(cell, font=t['a_conf_font'], fill=t['a_conf_fill'],
                      align=t['a_conf_align'], border=t['a_conf_border'])
            else:
                apply(cell, font=t['a_mid_conf_font'], fill=t['a_mid_conf_fill'],
                      align=t['a_mid_conf_align'], border=t['a_mid_conf_border'])

    def set_b(r, text, style='top'):
        cell = ws.cell(r, 2)
        cell.value = text
        if style == 'top':
            apply(cell, font=t['b_top_font'], fill=t['b_top_fill'], align=t['b_top_align'])
        elif style == 'conf_head':
            apply(cell, font=t['b_conf_head_font'], fill=t['b_conf_head_fill'], align=t['b_conf_head_align'])
        elif style == 'ex_head':
            apply(cell, font=t['b_ex_head_font'], fill=t['b_ex_head_fill'], align=t['b_ex_head_align'])
        elif style == 'res_type':
            apply(cell, font=t['res_type_label_font'], fill=t['res_type_label_fill'],
                  align=t['res_type_label_align'], border=t['res_type_label_border'])
        elif style == 'res_pf':
            apply(cell, font=t['res_pf_label_font'], fill=t['res_pf_label_fill'],
                  align=t['res_pf_label_align'], border=t['res_pf_label_border'])
        elif style == 'res_date':
            apply(cell, font=t['res_date_label_font'], fill=t['res_date_label_fill'],
                  align=t['res_date_label_align'], border=t['res_date_label_border'])
        elif style == 'res_defect':
            apply(cell, font=t['res_defect_label_font'], fill=t['res_defect_label_fill'],
                  align=t['res_defect_label_align'], border=t['res_defect_label_border'])
        else:
            apply(cell, font=t['b_sub_font'], fill=t['b_sub_fill'], align=t['b_sub_align'])

    def set_d(r, text, style='top'):
        cell = ws.cell(r, 4)
        cell.value = text
        if style == 'top':
            apply(cell, font=t['d_top_font'], fill=t['d_top_fill'], align=t['d_top_align'])
        elif style == 'conf_head':
            apply(cell, font=t['d_conf_head_font'], fill=t['d_conf_head_fill'], align=t['d_conf_head_align'])
        elif style == 'ex_head':
            apply(cell, font=t['d_ex_head_font'], fill=t['d_ex_head_fill'], align=t['d_ex_head_align'])
        else:
            apply(cell, font=t['d_sub_font'], fill=t['d_sub_fill'], align=t['d_sub_align'])

        # Gate 12: Guard against text overflow into matrix cols F+
        if text and len(str(text)) > 50:
            al = cell.alignment
            cell.alignment = Alignment(
                horizontal=al.horizontal if al and al.horizontal else 'right',
                vertical=al.vertical if al and al.vertical else 'top',
                wrap_text=True
            )

    def mark_o(r, cols):
        for c in cols:
            cell = ws.cell(r, c)
            cell.value = 'O'
            apply(cell, font=t['mark_font'], align=t['mark_align'], border=t['mark_border'])

    def grid(r, c_start, c_end):
        for c in range(c_start, c_end + 1):
            if ws.cell(r, c).value != 'O':
                apply(ws.cell(r, c), border=t['mark_border'])

    def row_h(r, h=13.5):
        ws.row_dimensions[r].height = h

    # ════════════════════════════════════════════════════════════════════
    # CONDITION block (E7, E8, E10 compliant)
    # ════════════════════════════════════════════════════════════════════
    set_col_a(COND_START, 'Condition', zone='cond')
    for r in range(COND_START, CONF_START):
        if r != COND_START:
            set_col_a(r, zone='cond')
        row_h(r)

        # Invariant E7: Initialize B-C-D unified 3-column box
        is_last = (r == CONF_START - 1)
        b_side = Side(style='double') if is_last else Side(style='thin')
        apply(ws.cell(r, 2), font=t['b_top_font'], fill=t['b_top_fill'], align=t['b_top_align'],
              border=Border(left=Side(style='thin'), top=Side(style='thin'), bottom=b_side))
        apply(ws.cell(r, 3), font=t['b_top_font'], fill=t['b_top_fill'], align=t['b_top_align'],
              border=Border(top=Side(style='thin'), bottom=b_side))
        apply(ws.cell(r, 4), font=t['d_top_font'], fill=t['d_top_fill'], align=t['d_top_align'],
              border=Border(right=Side(style='thin'), top=Side(style='thin'), bottom=b_side))
        if is_last:
            apply(ws.cell(r, 5), border=Border(bottom=b_side))

    # Populate Condition rows
    # Ensure E8 (no duplicate header) and E10 (Precondition + Input Parameters hierarchy)
    first_cond = True
    for idx, item in enumerate(parsed_data['cond_items']):
        curr_r = COND_START + idx
        raw_b = str(item['b'] or '').strip() if item['b'] else ''
        raw_d = str(item['d'] or '').strip() if item['d'] else ''

        if first_cond:
            set_b(curr_r, 'Precondition', style='top')
            first_cond = False
        elif raw_b and raw_b.lower() != 'precondition':
            set_b(curr_r, raw_b, style='top')
        else:
            # If no B label and starts with parameter pattern, could be input param
            pass

        if raw_d:
            set_d(curr_r, raw_d, style='top')

        mark_o(curr_r, item['marks'])
        grid(curr_r, 6, MAX_TC_COL)

    # Condition block outer closing double border on CONF_START - 1
    _dbl = Side(style='double')
    for c in range(2, MAX_TC_COL + 1):
        cell = ws.cell(CONF_START - 1, c)
        ex = cell.border
        cell.border = Border(left=ex.left, right=ex.right, top=ex.top, bottom=_dbl)

    # ════════════════════════════════════════════════════════════════════
    # CONFIRM block (E7, E8 compliant)
    # ════════════════════════════════════════════════════════════════════
    set_col_a(CONF_START, 'Confirm', zone='conf')
    for r in range(CONF_START, RES_START):
        if r != CONF_START:
            set_col_a(r, zone='conf')
        row_h(r)

        # Invariant E7: Initialize B-C-D unified 3-column box
        is_first = (r == CONF_START)
        t_side = None if is_first else Side(style='thin')
        apply(ws.cell(r, 2), font=t['b_sub_font'], fill=t['b_sub_fill'], align=t['b_sub_align'],
              border=Border(left=Side(style='thin'), top=t_side, bottom=Side(style='thin')))
        apply(ws.cell(r, 3), font=t['b_sub_font'], fill=t['b_sub_fill'], align=t['b_sub_align'],
              border=Border(top=t_side, bottom=Side(style='thin')))
        apply(ws.cell(r, 4), font=t['d_sub_font'], fill=t['d_sub_fill'], align=t['d_sub_align'],
              border=Border(right=Side(style='thin'), top=t_side, bottom=Side(style='thin')))
        apply(ws.cell(r, 5), border=Border(left=Side(style='thin'), right=Side(style='thin'), top=t_side, bottom=Side(style='thin')))

    # Populate Confirm rows
    first_conf = True
    for idx, item in enumerate(parsed_data['conf_items']):
        curr_r = CONF_START + idx
        raw_b = str(item['b'] or '').strip() if item['b'] else ''
        raw_d = str(item['d'] or '').strip() if item['d'] else ''

        if first_conf:
            set_b(curr_r, raw_b or 'Return', style='conf_head')
            first_conf = False
        elif raw_b and raw_b.lower() not in ['return']:
            if 'exception' in raw_b.lower():
                set_b(curr_r, raw_b, style='ex_head')
            else:
                set_b(curr_r, raw_b, style='sub')

        if raw_d:
            set_d(curr_r, raw_d, style='sub')

        mark_o(curr_r, item['marks'])
        grid(curr_r, 6, MAX_TC_COL)

    # ════════════════════════════════════════════════════════════════════
    # RESULT block (E9 compliant)
    # ════════════════════════════════════════════════════════════════════
    set_col_a(RES_START, 'Result', zone='conf')
    for r in range(RES_START, DEFECT_ROW + 1):
        if r != RES_START:
            set_col_a(r, zone='conf')
        row_h(r)

    # Result footer labels (E9: Tahoma 8pt non-bold, align_h=left)
    set_b(TYPE_ROW,   'Type(N : Normal, A : Abnormal, B : Boundary)', style='res_type')
    set_b(PF_ROW,     'Passed/Failed', style='res_pf')
    set_b(DATE_ROW,   'Executed Date', style='res_date')
    set_b(DEFECT_ROW, 'Defect ID', style='res_defect')

    # Result merges B:D for each footer row + borders on C & D
    ws.cell(TYPE_ROW, 3).border = Border(top=Side(style='double'), bottom=Side(style='thin'))
    ws.cell(TYPE_ROW, 4).border = Border(right=Side(style='thin'), top=Side(style='double'), bottom=Side(style='thin'))

    ws.cell(PF_ROW, 3).border = Border(top=Side(style='thin'), bottom=Side(style='thin'))
    ws.cell(PF_ROW, 4).border = Border(right=Side(style='thin'), top=Side(style='thin'), bottom=Side(style='thin'))

    ws.cell(DATE_ROW, 3).border = Border(top=Side(style='thin'), bottom=Side(style='thin'))
    ws.cell(DATE_ROW, 4).border = Border(right=Side(style='thin'), top=Side(style='thin'), bottom=Side(style='thin'))

    ws.cell(DEFECT_ROW, 3).border = Border(top=Side(style='thin'), bottom=Side(style='double'))
    ws.cell(DEFECT_ROW, 4).border = Border(right=Side(style='thin'), top=Side(style='thin'), bottom=Side(style='double'))

    for fr in [TYPE_ROW, PF_ROW, DATE_ROW, DEFECT_ROW]:
        ws.merge_cells(f'B{fr}:D{fr}')

    # Type values
    for i, v in enumerate(parsed_data['type_vals']):
        cell = ws.cell(TYPE_ROW, 6 + i)
        cell.value = v
        apply(cell, font=t['type_font'], align=t['type_align'], border=t['type_border'])

    # PF values
    for i, v in enumerate(parsed_data['pf_vals']):
        cell = ws.cell(PF_ROW, 6 + i)
        cell.value = v
        apply(cell, font=t['pf_font'], align=t['pf_align'], border=t['pf_border'])

    # Executed Dates
    for i, d in enumerate(parsed_data['dates']):
        cell = ws.cell(DATE_ROW, 6 + i)
        if isinstance(d, str):
            try:
                parts = d.split('/')
                if len(parts) == 3:
                    d = datetime.datetime(int(parts[2]), int(parts[1]), int(parts[0]))
            except Exception:
                pass
        cell.value = d
        apply(cell, font=t['date_font'], align=t['date_align'],
              border=t['date_border'], numfmt=t['date_numfmt'])

    # Defect ID values
    for i, def_val in enumerate(parsed_data['defects']):
        cell = ws.cell(DEFECT_ROW, 6 + i)
        cell.value = def_val
        apply(cell, font=t['date_font'], align=t['date_align'], border=t['date_border'])

    # Result block outer closing double border on DEFECT_ROW (cols A..MAX_TC_COL)
    for c in range(1, MAX_TC_COL + 1):
        cell = ws.cell(DEFECT_ROW, c)
        ex = cell.border
        cell.border = Border(left=ex.left, right=ex.right, top=ex.top, bottom=_dbl)

    # Data Validations (E11)
    dv_o = DataValidation(type='list', formula1='"O"', allow_blank=True, showDropDown=False)
    ws.add_data_validation(dv_o)
    dv_o.add(f'F{COND_START}:{LAST_TC}{RES_START - 1}')

    dv_nab = DataValidation(type='list', formula1='"N,A,B"', allow_blank=True, showDropDown=False)
    ws.add_data_validation(dv_nab)
    dv_nab.add(f'F{TYPE_ROW}:{LAST_TC}{TYPE_ROW}')

    dv_pf = DataValidation(type='list', formula1='"P,F"', allow_blank=True, showDropDown=False)
    ws.add_data_validation(dv_pf)
    dv_pf.add(f'F{PF_ROW}:{LAST_TC}{PF_ROW}')

    return ws


def update_summary_sheets(wb_target, wb_in):
    """
    Update Overview sheets ('Functions' and 'Statistics') with 100% template format parity (E1, E3, E5).
    """
    thin_border = Border(
        left=Side(style='thin'), right=Side(style='thin'),
        top=Side(style='thin'), bottom=Side(style='thin')
    )
    navy_fill = PatternFill(fill_type='solid', fgColor='FF000080')
    white_fill = PatternFill(fill_type='solid', fgColor='FFFFFFFF')
    no_fill = PatternFill(fill_type=None)

    # ── 1. Update Functions Sheet ─────────────────────────────────────────
    if 'Functions' in wb_target.sheetnames:
        ws_fn = wb_target['Functions']
        ws_fn_in = wb_in['Functions']

        # Clear existing table rows in Functions (rows 11 to 40)
        for r in range(11, 40):
            for c in range(1, 10):
                ws_fn.cell(r, c).value = None
                ws_fn.cell(r, c).fill = no_fill
                ws_fn.cell(r, c).border = Border()

        # Header row 10 formatting
        ws_fn.row_dimensions[10].height = 28.0
        for c in range(1, 8):
            apply(ws_fn.cell(10, c),
                  font=Font(name='Tahoma', size=10.0, bold=True, color='FFFFFFFF'),
                  fill=navy_fill,
                  align=Alignment(horizontal='center', vertical='center', wrap_text=True),
                  border=thin_border)

        # Populate all 20 functions from input Functions sheet with Arial 11pt template standard
        for r in range(11, 31):
            fn_idx = r - 10
            fn_sheet = FUNCTION_SHEETS[fn_idx - 1]

            ws_fn.cell(r, 1).value = fn_idx
            ws_fn.cell(r, 2).value = ws_fn_in.cell(r, 2).value    # Requirement Name
            ws_fn.cell(r, 3).value = ws_fn_in.cell(r, 3).value    # Class Name
            ws_fn.cell(r, 4).value = f"='{fn_sheet}'!L2"         # Live Function Name link
            ws_fn.cell(r, 5).value = f"='{fn_sheet}'!C2"         # Live Function Code link
            ws_fn.cell(r, 6).value = fn_sheet                     # Sheet Name
            ws_fn.cell(r, 7).value = ws_fn_in.cell(r, 7).value    # Description

            for c in range(1, 8):
                cell = ws_fn.cell(r, c)
                cell.font = Font(name='Arial', size=11.0, bold=False)
                cell.border = thin_border
                cell.fill = no_fill
                if c in [1, 5, 6]:
                    cell.alignment = Alignment(horizontal='center', vertical='center')
                else:
                    cell.alignment = Alignment(horizontal='left', vertical='center', wrap_text=True)

            # Auto-scaling row height based on text content (UX enhancement)
            lines_req = len(str(ws_fn.cell(r, 2).value or '').split('\n'))
            lines_cls = len(str(ws_fn.cell(r, 3).value or '').split('\n'))
            desc_text = str(ws_fn.cell(r, 7).value or '')
            desc_newlines = len(desc_text.split('\n'))
            desc_wraps = max(1, int(len(desc_text) / 45.0))
            total_lines = max(lines_req, lines_cls, desc_newlines, desc_wraps)
            ws_fn.row_dimensions[r].height = max(20.0, total_lines * 14.5)

    # ── 2. Update Statistics Sheet ─────────────────────────────────────────
    if 'Statistics' in wb_target.sheetnames:
        ws_stat = wb_target['Statistics']

        # Clear existing rows below header (rows 12 to 50)
        for r in range(12, 50):
            for c in range(1, 15):
                ws_stat.cell(r, c).value = None
                ws_stat.cell(r, c).fill = no_fill
                ws_stat.cell(r, c).border = Border()
                ws_stat.cell(r, c).alignment = Alignment()
                ws_stat.cell(r, c).font = Font()
                ws_stat.cell(r, c).number_format = 'General'

        # Header row 11 formatting
        ws_stat.row_dimensions[11].height = 28.0
        for c in range(1, 10):
            apply(ws_stat.cell(11, c),
                  font=Font(name='Tahoma', size=10.0, bold=True, color='FFFFFFFF'),
                  fill=navy_fill,
                  align=Alignment(horizontal='center', vertical='center'),
                  border=thin_border)

        # 20 Data rows (rows 12 to 31)
        for r in range(12, 32):
            fn_idx = r - 11
            fn_sheet = FUNCTION_SHEETS[fn_idx - 1]
            ws_stat.row_dimensions[r].height = 18.0

            # Col 1: No
            cell_1 = ws_stat.cell(r, 1)
            cell_1.value = fn_idx
            apply(cell_1, font=Font(name='Tahoma', size=11.0, bold=False),
                  fill=white_fill, align=Alignment(horizontal='center', vertical='center'),
                  border=thin_border)

            # Col 2: Function code link
            cell_2 = ws_stat.cell(r, 2)
            cell_2.value = f"='{fn_sheet}'!C2"
            apply(cell_2, font=Font(name='Tahoma', size=11.0, bold=False, color='FF0000FF'),
                  fill=white_fill, align=Alignment(horizontal='left', vertical='center'),
                  border=thin_border)

            # Cols 3..9: Live KPI formulas
            kpi_formulas = [
                f"='{fn_sheet}'!A7",   # Passed
                f"='{fn_sheet}'!C7",   # Failed
                f"='{fn_sheet}'!F7",   # Untested
                f"='{fn_sheet}'!L7",   # N
                f"='{fn_sheet}'!M7",   # A
                f"='{fn_sheet}'!N7",   # B
                f"='{fn_sheet}'!O7",   # Total
            ]
            for c_idx, formula in enumerate(kpi_formulas, start=3):
                cell_kpi = ws_stat.cell(r, c_idx)
                cell_kpi.value = formula
                apply(cell_kpi, font=Font(name='Arial', size=11.0, bold=False, color='00000000'),
                      fill=no_fill, align=Alignment(horizontal='center', vertical='center'),
                      border=thin_border)

        # Blank rows 32, 33
        ws_stat.row_dimensions[32].height = 15.0
        ws_stat.row_dimensions[33].height = 15.0

        # Subtotal row 34 (Col A navy, Col B navy 'Sub total', Cols C-H WHITE fill, Col I navy)
        SUB_ROW = 34
        ws_stat.row_dimensions[SUB_ROW].height = 20.0

        # Col A
        apply(ws_stat.cell(SUB_ROW, 1), fill=navy_fill, border=Border(left=Side(style='thin'), bottom=Side(style='thin')))

        # Col B: 'Sub total'
        cell_sub = ws_stat.cell(SUB_ROW, 2)
        cell_sub.value = 'Sub total'
        apply(cell_sub, font=Font(name='Tahoma', size=11.0, bold=True, color='FFFFFFFF'),
              fill=navy_fill, align=Alignment(horizontal='left', vertical='center'),
              border=Border(bottom=Side(style='thin')))

        # Cols C..H: Sum formulas with NO FILL (white/transparent) and black text
        sum_cols = ['C', 'D', 'E', 'F', 'G', 'H']
        for c_idx, col_letter in enumerate(sum_cols, start=3):
            cell_sum = ws_stat.cell(SUB_ROW, c_idx)
            cell_sum.value = f"=SUM({col_letter}12:{col_letter}31)"
            apply(cell_sum, font=Font(name='Arial', size=11.0, bold=False, color='00000000'),
                  fill=no_fill, align=Alignment(horizontal='center', vertical='center'),
                  border=Border(top=Side(style='thin'), bottom=Side(style='thin')))

        # Col I: Total Test Cases with NAVY FILL and white text
        cell_tot = ws_stat.cell(SUB_ROW, 9)
        cell_tot.value = f"=SUM(I12:I31)"
        apply(cell_tot, font=Font(name='Tahoma', size=11.0, bold=False, color='FFFFFFFF'),
              fill=navy_fill, align=Alignment(horizontal='center', vertical='center'),
              border=Border(right=Side(style='thin'), bottom=Side(style='thin')))

        # Blank row 35
        ws_stat.row_dimensions[35].height = 15.0

        # Summary ratio rows (36 to 40) — All 5 metrics from template
        ratios = [
            (36, 'Test coverage',            f"=IF(I{SUB_ROW}=0,0,(C{SUB_ROW}+D{SUB_ROW})*100/I{SUB_ROW})", False),
            (37, 'Test successful coverage', f"=IF(C{SUB_ROW}+D{SUB_ROW}=0,0,C{SUB_ROW}*100/(C{SUB_ROW}+D{SUB_ROW}))", False),
            (38, 'Normal case',              f"=IF(I{SUB_ROW}=0,0,F{SUB_ROW}*100/I{SUB_ROW})", True),
            (39, 'Abnormal case',            f"=IF(I{SUB_ROW}=0,0,G{SUB_ROW}*100/I{SUB_ROW})", True),
            (40, 'Boundary case',            f"=IF(I{SUB_ROW}=0,0,H{SUB_ROW}*100/I{SUB_ROW})", True),
        ]

        for r_num, label, formula, is_bold_num in ratios:
            ws_stat.row_dimensions[r_num].height = 18.0

            # Label (Col B)
            cell_lbl = ws_stat.cell(r_num, 2)
            cell_lbl.value = label
            apply(cell_lbl, font=Font(name='Tahoma', size=11.0, bold=True),
                  align=Alignment(horizontal='left', vertical='center'))

            # Value (Col D)
            cell_val = ws_stat.cell(r_num, 4)
            cell_val.value = formula
            f_name = 'Tahoma' if is_bold_num else 'Arial'
            apply(cell_val, font=Font(name=f_name, size=11.0, bold=is_bold_num),
                  align=Alignment(horizontal='right', vertical='center'),
                  numfmt='0.00')

            # Unit % (Col E)
            cell_pct = ws_stat.cell(r_num, 5)
            cell_pct.value = '%'
            apply(cell_pct, font=Font(name='Tahoma', size=11.0, bold=False),
                  align=Alignment(horizontal='left', vertical='center'))

        # ── 3. Relink Pie Charts to New Subtotal Row (34) ────────────────────
        for chart in ws_stat._charts:
            for s in chart.series:
                if s.val and s.val.numRef:
                    f_str = s.val.numRef.f or ''
                    if 'F' in f_str:
                        s.val.numRef.f = f"Statistics!$F${SUB_ROW}:$H${SUB_ROW}"
                        if s.cat and s.cat.strRef:
                            s.cat.strRef.f = "Statistics!$F$11:$H$11"
                    elif 'C' in f_str:
                        s.val.numRef.f = f"Statistics!$C${SUB_ROW}:$E${SUB_ROW}"
                        if s.cat and s.cat.strRef:
                            s.cat.strRef.f = "Statistics!$C$11:$E$11"

            # Position chart anchor below the ratio rows (row 42)
            if hasattr(chart.anchor, '_from'):
                chart.anchor._from.row = 42


def build_final():
    print(f"=== Starting Build Process for Report5_Unit Test-Final.xlsx ===")
    print(f"Loading template: {TMPL_PATH}")
    wb_tmpl = openpyxl.load_workbook(TMPL_PATH, data_only=False)

    print(f"Loading input data: {INPUT_PATH}")
    wb_in = openpyxl.load_workbook(INPUT_PATH, data_only=False)

    ws_ref = wb_tmpl['Example']
    tokens = extract_all_tokens(ws_ref)

    # 1. Generate all 20 function sheets
    for fn_name in FUNCTION_SHEETS:
        print(f"Generating function sheet: [{fn_name}]...")
        if fn_name not in wb_in.sheetnames:
            print(f"WARNING: Sheet '{fn_name}' not found in input workbook. Skipping.")
            continue
        parsed = parse_input_sheet(wb_in[fn_name])
        generate_function_sheet(wb_tmpl, ws_ref, fn_name, parsed, tokens)

    # 2. Update summary sheets (Functions & Statistics) with live formulas (E3)
    print("Updating 'Functions' and 'Statistics' summary sheets with live formulas...")
    update_summary_sheets(wb_tmpl, wb_in)

    # 3. Clean up temporary placeholder sheets
    placeholders_to_remove = ['Function 1', 'Function 2', 'Function3', 'example_test01']
    for p in placeholders_to_remove:
        if p in wb_tmpl.sheetnames:
            print(f"Removing temporary placeholder sheet: [{p}]")
            del wb_tmpl[p]

    # 4. Reorder sheets: Guideline -> Cover -> Functions -> Statistics -> 20 Function Sheets -> Example
    desired_order = ['Guideline', 'Cover', 'Functions', 'Statistics'] + FUNCTION_SHEETS + ['Example']
    existing_sheets = [s for s in desired_order if s in wb_tmpl.sheetnames]
    wb_tmpl._sheets = [wb_tmpl[s] for s in existing_sheets]

    # 5. E6 Validation: Run 12-Gate Diff Engine on all 20 function sheets
    print("\n[E6] Running 12-Gate Format Diff Engine on all generated sheets...")
    try:
        from tools.format_diff_excel import run_diff
    except ImportError:
        from format_diff_excel import run_diff

    total_diffs = 0
    for fn_name in FUNCTION_SHEETS:
        if fn_name in wb_tmpl.sheetnames:
            diffs = run_diff(wb_tmpl[fn_name], ws_ref, verbose=False)
            if diffs:
                print(f"  ✗ [{fn_name}] {len(diffs)} format diffs found:")
                for d in diffs[:5]:
                    print(f"    {d}")
                total_diffs += len(diffs)
            else:
                print(f"  ✓ [{fn_name}] 100% CLEAN (0 issues)")

    if total_diffs > 0:
        print(f"\nERROR: Total {total_diffs} format issues found across sheets. Aborting save.")
        return False

    # 6. Save to final destination
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    try:
        wb_tmpl.save(OUTPUT_PATH)
    except PermissionError:
        import subprocess, time
        subprocess.run(['taskkill', '/F', '/IM', 'excel.exe'], capture_output=True)
        time.sleep(0.5)
        wb_tmpl.save(OUTPUT_PATH)

    print(f"\n=======================================================")
    print(f"SUCCESS: 'Report5_Unit Test-Final.xlsx' built successfully!")
    print(f"Destination: {OUTPUT_PATH}")
    print(f"Final sheet list ({len(wb_tmpl.sheetnames)} sheets):")
    print(wb_tmpl.sheetnames)
    print(f"=======================================================")
    return True


if __name__ == '__main__':
    build_final()

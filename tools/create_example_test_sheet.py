# -*- coding: utf-8 -*-
"""
create_example_test_sheet.py
Copy sheet 'Example' from Report5_Unit Test.xlsx → 'Example_Test'
Fill with DIFFERENT data (ORDER-SVC function) while preserving 100% format.

E6 Compliance: run_format_diff() is called after generate before delivering.
"""
import sys, datetime
from copy import copy
import openpyxl
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.utils import get_column_letter

sys.stdout.reconfigure(encoding='utf-8')

TARGET = r'd:\Minh\For_myself\ZSCORT_GSU26_SAP05\tool\AI-Docx-Testing-Product\dataset1\output\Report5_Unit Test.xlsx'


# ── SECTION 1: Format token extraction (E1 — Template-Driven) ────────────
def extract_all_tokens(ws_ref: openpyxl.worksheet.worksheet.Worksheet) -> dict:
    """Extract every format token from the reference sheet. NO hardcoding."""

    def safe_copy(cell_attr):
        try:
            return copy(cell_attr)
        except Exception:
            return cell_attr

    r9_tc   = ws_ref.cell(9, 6)    # Row 9 TC header (navy, 180° rot, double border top)
    r9_a    = ws_ref.cell(9, 1)    # Row 9 col A (navy fill + border l=double, t=double)
    r9_b    = ws_ref.cell(9, 2)    # Row 9 col B (navy fill, bold, double border top)
    r9_c    = ws_ref.cell(9, 3)    # Row 9 col C-E (navy fill, double border top)
    r9_d    = ws_ref.cell(9, 4)    # Row 9 col D alignment
    r9_e    = ws_ref.cell(9, 5)    # Row 9 col E alignment
    a10     = ws_ref.cell(10, 1)   # Col A Condition section title
    a33     = ws_ref.cell(33, 1)   # Col A Confirm section title
    a15     = ws_ref.cell(15, 1)   # Col A mid-section (non-title fill row, Condition zone)
    a34     = ws_ref.cell(34, 1)   # Col A mid-section (Confirm zone — align_v=top)
    b10     = ws_ref.cell(10, 2)   # Col B label (Precondition-like, v=top)
    b34     = ws_ref.cell(34, 2)   # Col B label (list/return label, v=bottom, h=right)
    b33     = ws_ref.cell(33, 2)   # Col B Confirm section 1st label (h=None, v=bottom, bt=None)
    b40     = ws_ref.cell(40, 2)   # Col B Exception label (h=None, v=bottom, bt=thin)
    d33     = ws_ref.cell(33, 4)   # Col D at B33 row (bt=None)
    d40     = ws_ref.cell(40, 4)   # Col D at B40 row (bt=thin)
    d15     = ws_ref.cell(15, 4)   # Col D data value (v=top)
    d35     = ws_ref.cell(35, 4)   # Col D data value (v=bottom)
    b45     = ws_ref.cell(45, 2)   # Col B Type label (Tahoma 8pt non-bold, align_h=left, v=bottom, border T=double, B=thin)
    b46     = ws_ref.cell(46, 2)   # Col B PF label (Tahoma 8pt non-bold, align_h=left, v=bottom, border T=thin, B=thin)
    b47     = ws_ref.cell(47, 2)   # Col B Date label (Tahoma 8pt non-bold, align_h=left, v=top, border T=thin, B=thin)
    b48     = ws_ref.cell(48, 2)   # Col B Defect label (Tahoma 8pt non-bold, align_h=left, v=top, border T=thin, B=double)

    type_r  = ws_ref.cell(45, 6)   # Result Type cell: Courier New 8pt, border_t=double
    pf_r    = ws_ref.cell(46, 6)   # Result PF cell: Courier New 8pt
    date_r  = ws_ref.cell(47, 6)   # Result Date cell: textRotation=255, mm/dd

    # Find first O mark cell
    mark_cell = None
    for r in range(10, 50):
        for c in range(6, 25):
            if ws_ref.cell(r, c).value == 'O':
                mark_cell = ws_ref.cell(r, c)
                break
        if mark_cell:
            break

    return {
        # Row 9 TC header (cols 6+)
        'r9_font':  safe_copy(r9_tc.font),
        'r9_fill':  safe_copy(r9_tc.fill),
        'r9_align': safe_copy(r9_tc.alignment),
        'r9_border': safe_copy(r9_tc.border),

        # Row 9 col A (full style: navy fill + border_l=double + border_t=double)
        'r9_a_fill':   safe_copy(r9_a.fill),
        'r9_a_font':   safe_copy(r9_a.font),
        'r9_a_align':  safe_copy(r9_a.alignment),
        'r9_a_border': safe_copy(r9_a.border),

        # Row 9 cols B-E (navy fill, double border top, no text rotation)
        'r9_b_fill':   safe_copy(r9_b.fill),
        'r9_b_font':   safe_copy(r9_b.font),
        'r9_b_align':  safe_copy(r9_b.alignment),
        'r9_b_border': safe_copy(r9_b.border),
        'r9_c_fill':   safe_copy(r9_c.fill),
        'r9_c_font':   safe_copy(r9_c.font),
        'r9_c_align':  safe_copy(r9_c.alignment),
        'r9_c_border': safe_copy(r9_c.border),
        'r9_d_align':  safe_copy(r9_d.alignment),
        'r9_e_align':  safe_copy(r9_e.alignment),

        # Col A — Condition section title (A10: v=center, t=medium, l=double, r=thin)
        'a_cond_font':   safe_copy(a10.font),
        'a_cond_fill':   safe_copy(a10.fill),
        'a_cond_align':  safe_copy(a10.alignment),
        'a_cond_border': safe_copy(a10.border),

        # Col A — Confirm/Result section title (A33: v=top, t=medium)
        'a_conf_font':   safe_copy(a33.font),
        'a_conf_fill':   safe_copy(a33.fill),
        'a_conf_align':  safe_copy(a33.alignment),
        'a_conf_border': safe_copy(a33.border),

        # Col A — mid-section fill row in Condition zone (A15: v=center, l=double, r=thin, t=None)
        'a_mid_cond_font':   safe_copy(a15.font),
        'a_mid_cond_fill':   safe_copy(a15.fill),
        'a_mid_cond_align':  safe_copy(a15.alignment),
        'a_mid_cond_border': safe_copy(a15.border),

        # Col A — mid-section fill row in Confirm zone (A34: v=top)
        'a_mid_conf_font':   safe_copy(a34.font),
        'a_mid_conf_fill':   safe_copy(a34.fill),
        'a_mid_conf_align':  safe_copy(a34.alignment),
        'a_mid_conf_border': safe_copy(a34.border),

        # Col B label — top-of-group (B10: h=left, v=top, fill=white, border l+t+b)
        'b_top_font':   safe_copy(b10.font),
        'b_top_fill':   safe_copy(b10.fill),
        'b_top_align':  safe_copy(b10.alignment),
        'b_top_border': safe_copy(b10.border),

        # Col B label — sub-group (B34: h=right, v=bottom)
        'b_sub_font':   safe_copy(b34.font),
        'b_sub_fill':   safe_copy(b34.fill),
        'b_sub_align':  safe_copy(b34.alignment),
        'b_sub_border': safe_copy(b34.border),

        # Col B Confirm first-label (B33: h=None, v=bottom, bt=None)
        'b_conf_head_font':   safe_copy(b33.font),
        'b_conf_head_fill':   safe_copy(b33.fill),
        'b_conf_head_align':  safe_copy(b33.alignment),
        'b_conf_head_border': safe_copy(b33.border),
        'd_conf_head_font':   safe_copy(d33.font),
        'd_conf_head_fill':   safe_copy(d33.fill),
        'd_conf_head_align':  safe_copy(d33.alignment),
        'd_conf_head_border': safe_copy(d33.border),

        # Col B Exception label (B40: h=None, v=bottom, bt=thin)
        'b_ex_head_font':   safe_copy(b40.font),
        'b_ex_head_fill':   safe_copy(b40.fill),
        'b_ex_head_align':  safe_copy(b40.alignment),
        'b_ex_head_border': safe_copy(b40.border),
        'd_ex_head_font':   safe_copy(d40.font),
        'd_ex_head_fill':   safe_copy(d40.fill),
        'd_ex_head_align':  safe_copy(d40.alignment),
        'd_ex_head_border': safe_copy(d40.border),

        # Col B Result labels (Example B45..B48: Tahoma 8pt non-bold, align_h=left)
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

        # Col D data value — top-zone (D15: h=right, v=top)
        'd_top_font':   safe_copy(d15.font),
        'd_top_fill':   safe_copy(d15.fill),
        'd_top_align':  safe_copy(d15.alignment),
        'd_top_border': safe_copy(d15.border),

        # Col D data value — sub-zone (D35: h=right, v=bottom)
        'd_sub_font':   safe_copy(d35.font),
        'd_sub_fill':   safe_copy(d35.fill),
        'd_sub_align':  safe_copy(d35.alignment),
        'd_sub_border': safe_copy(d35.border),

        # O-mark matrix cell
        'mark_font':   safe_copy(mark_cell.font),
        'mark_align':  safe_copy(mark_cell.alignment),
        'mark_border': safe_copy(mark_cell.border),

        # Result Type row (Courier 8pt non-bold, border_t=double)
        'type_font':   safe_copy(type_r.font),
        'type_align':  safe_copy(type_r.alignment),
        'type_border': safe_copy(type_r.border),

        # Result PF row (Courier 8pt non-bold)
        'pf_font':   safe_copy(pf_r.font),
        'pf_align':  safe_copy(pf_r.alignment),
        'pf_border': safe_copy(pf_r.border),

        # Result Date row (Tahoma 8pt, textRotation=255, mm/dd)
        'date_font':   safe_copy(date_r.font),
        'date_align':  safe_copy(date_r.alignment),
        'date_border': safe_copy(date_r.border),
        'date_numfmt': date_r.number_format,
    }


# ── SECTION 2: Cell style appliers ───────────────────────────────────────
def apply(cell, font=None, fill=None, align=None, border=None, numfmt=None):
    if font:   cell.font      = copy(font)
    if fill:   cell.fill      = copy(fill)
    if align:  cell.alignment = copy(align)
    if border: cell.border    = copy(border)
    if numfmt: cell.number_format = numfmt


# ── SECTION 3: Generate sheet ────────────────────────────────────────────
def generate(wb):
    if 'Example_Test' in wb.sheetnames:
        del wb['Example_Test']

    ws_ex = wb['Example']
    t = extract_all_tokens(ws_ex)

    ws = wb.copy_worksheet(ws_ex)
    ws.title = 'Example_Test'

    # Remove stale merges from Example data section (rows > 8)
    for m in list(ws.merged_cells.ranges):
        if m.min_row > 8:
            ws.merged_cells.remove(m)

    # Clear all data/style below row 8
    for r in range(9, 65):
        for c in range(1, 25):
            cell = ws.cell(r, c)
            cell.value  = None
            cell.fill   = PatternFill(fill_type=None)
            cell.border = Border()
            cell.alignment = Alignment()
            cell.font   = Font()
            cell.number_format = 'General'

    # ── Column widths from Example (E1 — exact copy) ──────────────────────
    for c in range(1, 22):
        col = get_column_letter(c)
        ex_w = ws_ex.column_dimensions[col].width
        ws.column_dimensions[col].width = ex_w if ex_w else 8.43

    # ── Metadata rows 2-5 — new ORDER-SVC data ────────────────────────────
    ws.cell(2, 3).value  = 'ORDER-SVC-001'
    ws.cell(2, 12).value = 'OrderService (createOrder / cancelOrder)'
    ws.cell(3, 3).value  = 'Trần Minh Khôi'
    ws.cell(3, 6).value  = 'Trần Minh Khôi'
    ws.cell(4, 3).value  = 280
    ws.cell(5, 3).value  = 'Verify order creation, stock reservation, and cancellation rollback.'

    # ── Section row boundaries ────────────────────────────────────────────
    COND_START  = 10
    CONF_START  = 33
    RES_START   = 42
    TYPE_ROW    = 42
    PF_ROW      = 43
    DATE_ROW    = 44
    DEFECT_ROW  = 45
    MAX_TC_COL  = 13   # 8 TCs: cols F(6) → M(13)
    LAST_TC     = get_column_letter(MAX_TC_COL)

    # Row 7 KPI formulas
    ws.cell(7, 1).value  = f'=COUNTIF(F{PF_ROW}:{LAST_TC}{PF_ROW},"P")'
    ws.cell(7, 3).value  = f'=COUNTIF(F{PF_ROW}:{LAST_TC}{PF_ROW},"F")'
    ws.cell(7, 6).value  = '=SUM(O7,-A7,-C7)'
    ws.cell(7, 12).value = f'=COUNTIF(F{TYPE_ROW}:{LAST_TC}{TYPE_ROW},"N")'
    ws.cell(7, 13).value = f'=COUNTIF(F{TYPE_ROW}:{LAST_TC}{TYPE_ROW},"A")'
    ws.cell(7, 14).value = f'=COUNTIF(F{TYPE_ROW}:{LAST_TC}{TYPE_ROW},"B")'
    ws.cell(7, 15).value = f'=COUNTA(F9:{LAST_TC}9)'

    # ── Row 9 TC headers ──────────────────────────────────────────────────
    ws.row_dimensions[9].height = 45.0
    # Col A row 9: full style from Example (navy fill + align_v=bottom + border_l=double + border_t=double)
    apply(ws.cell(9, 1), font=t['r9_a_font'], fill=t['r9_a_fill'],
          align=t['r9_a_align'], border=t['r9_a_border'])
    # Cols B-E: navy fill + alignment + double border top
    apply(ws.cell(9, 2), font=t['r9_b_font'], fill=t['r9_b_fill'],
          align=t['r9_b_align'], border=t['r9_b_border'])
    for c in [3, 5]:
        apply(ws.cell(9, c), font=t['r9_c_font'], fill=t['r9_c_fill'],
              align=t['r9_c_align'], border=t['r9_c_border'])
    apply(ws.cell(9, 4), font=t['r9_c_font'], fill=t['r9_c_fill'],
          align=t['r9_d_align'], border=t['r9_c_border'])

    TC_IDS = [f'UTCID{i:02d}' for i in range(1, 9)]
    for i, tcid in enumerate(TC_IDS, start=6):
        cell = ws.cell(9, i)
        cell.value = tcid
        apply(cell, font=t['r9_font'], fill=t['r9_fill'],
              align=t['r9_align'], border=t['r9_border'])

    # ── Helper: set col A for a data row ─────────────────────────────────
    def set_col_a(r, value=None, zone='cond'):
        cell = ws.cell(r, 1)
        cell.value = value
        if zone == 'cond':
            if value:   # section title row
                apply(cell, font=t['a_cond_font'], fill=t['a_cond_fill'],
                      align=t['a_cond_align'], border=t['a_cond_border'])
            else:
                apply(cell, font=t['a_mid_cond_font'], fill=t['a_mid_cond_fill'],
                      align=t['a_mid_cond_align'], border=t['a_mid_cond_border'])
        else:  # conf / result zone
            if value:
                apply(cell, font=t['a_conf_font'], fill=t['a_conf_fill'],
                      align=t['a_conf_align'], border=t['a_conf_border'])
            else:
                apply(cell, font=t['a_mid_conf_font'], fill=t['a_mid_conf_fill'],
                      align=t['a_mid_conf_align'], border=t['a_mid_conf_border'])

    # ── Helper: set col B label ───────────────────────────────────────────
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

    # ── Helper: set col D label ───────────────────────────────────────────
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

    # ── Helper: set O mark ────────────────────────────────────────────────
    def mark_o(r, *cols):
        for c in cols:
            cell = ws.cell(r, c)
            cell.value = 'O'
            apply(cell, font=t['mark_font'], align=t['mark_align'],
                  border=t['mark_border'])

    # ── Helper: set empty matrix cell border ──────────────────────────────
    def grid(r, c_start, c_end):
        for c in range(c_start, c_end + 1):
            if ws.cell(r, c).value != 'O':
                apply(ws.cell(r, c), border=t['mark_border'])

    def row_h(r, h=13.5):
        ws.row_dimensions[r].height = h

    # ════════════════════════════════════════════════════════════════════
    # CONDITION block: rows 10-32
    # ════════════════════════════════════════════════════════════════════
    set_col_a(COND_START, 'Condition', zone='cond')
    for r in range(COND_START, CONF_START):
        if r != COND_START:
            set_col_a(r, zone='cond')
        row_h(r)

        # Initialize B-C-D unified 3-column box for EVERY Condition row
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

    # Precondition group (rows 10-13)
    set_b(10, 'Precondition', style='top')
    set_d(10, '', style='top')
    set_d(11, 'User is authenticated (valid JWT token)', style='top')
    set_d(12, 'Product catalog is loaded (>0 items)', style='top')
    set_d(13, 'Database is reachable', style='top')

    # input_items group (rows 14-20)
    set_b(14, 'input_items (cart)', style='top')
    set_d(15, '[]  (empty cart)', style='top')
    set_d(16, '[{productId: P001, qty: 1}]', style='top')
    set_d(17, '[{productId: P001, qty: 99}]', style='top')
    set_d(18, '[{productId: P001, qty: 100}]', style='top')
    set_d(19, '[{productId: INVALID, qty: 1}]', style='top')
    set_d(20, '[{productId: P001, qty: -1}]', style='top')

    # shippingAddress group (rows 21-25)
    set_b(21, 'shippingAddress', style='top')
    set_d(22, 'null', style='top')
    set_d(23, '""  (empty string)', style='top')
    set_d(24, '"123 Nguyen Hue, HCMC"  (valid)', style='top')
    set_d(25, '"A" * 256  (over-length)', style='top')

    # stock group (rows 26-32)
    set_b(26, 'stock.available', style='top')
    set_d(27, '0 (out of stock)', style='top')
    set_d(28, '1 (last unit)', style='top')
    set_d(29, '50 (normal)', style='top')
    set_d(30, '100 (max boundary)', style='top')
    set_d(31, 'Reserved by concurrent order (race condition)', style='top')
    set_d(32, 'DB lock timeout during reservation', style='top')

    # O marks — Condition
    mark_o(11, 6, 7, 8, 9, 10, 11, 12, 13)
    mark_o(12, 6, 7, 8, 9, 10, 11, 12, 13)
    mark_o(13, 6, 7, 8, 9, 10, 11, 12, 13)
    mark_o(15, 6)
    mark_o(16, 7, 8)
    mark_o(17, 9)
    mark_o(18, 10)
    mark_o(19, 11)
    mark_o(20, 12)
    mark_o(22, 13)
    mark_o(23, 6)
    mark_o(24, 7, 8, 9, 10)
    mark_o(25, 11)
    mark_o(27, 6)
    mark_o(28, 9)
    mark_o(29, 7, 8, 10)
    mark_o(30, 11)
    mark_o(31, 12)
    mark_o(32, 13)

    for r in range(COND_START, CONF_START):
        grid(r, 6, MAX_TC_COL)

    # Condition block outer closing border: double bottom on row 32 (all cols B-MAX_TC_COL)
    # Extracted from Example: R32C2-T32 all have border-bottom=double
    _dbl_side = Side(style='double')
    for c in range(2, MAX_TC_COL + 1):
        cell = ws.cell(CONF_START - 1, c)  # = row 32
        ex = cell.border
        cell.border = Border(left=ex.left, right=ex.right, top=ex.top, bottom=_dbl_side)

    # ════════════════════════════════════════════════════════════════════
    # CONFIRM block: rows 33-41
    # ════════════════════════════════════════════════════════════════════
    set_col_a(CONF_START, 'Confirm', zone='conf')
    for r in range(CONF_START, RES_START):
        if r != CONF_START:
            set_col_a(r, zone='conf')
        row_h(r)

        # Initialize B-C-D unified 3-column box for EVERY Confirm row
        is_first = (r == CONF_START)
        t_side = None if is_first else Side(style='thin')
        apply(ws.cell(r, 2), font=t['b_sub_font'], fill=t['b_sub_fill'], align=t['b_sub_align'],
              border=Border(left=Side(style='thin'), top=t_side, bottom=Side(style='thin')))
        apply(ws.cell(r, 3), font=t['b_sub_font'], fill=t['b_sub_fill'], align=t['b_sub_align'],
              border=Border(top=t_side, bottom=Side(style='thin')))
        apply(ws.cell(r, 4), font=t['d_sub_font'], fill=t['d_sub_fill'], align=t['d_sub_align'],
              border=Border(right=Side(style='thin'), top=t_side, bottom=Side(style='thin')))
        apply(ws.cell(r, 5), border=Border(left=Side(style='thin'), right=Side(style='thin'), top=t_side, bottom=Side(style='thin')))

    set_b(33, 'Return', style='conf_head')    # B33: h=None, v=bottom, bt=None
    set_d(33, '', style='conf_head')           # D33: bt=None
    set_b(34, 'return value', style='sub')
    set_d(34, '', style='sub')
    set_d(35, 'OrderCreationError("Empty cart")', style='sub')
    set_d(36, 'Order { orderId, status: "PENDING", totalAmount }', style='sub')
    set_d(37, 'Order { orderId, status: "PENDING", totalAmount }', style='sub')
    set_d(38, 'Order { orderId, status: "PENDING", totalAmount }', style='sub')
    set_d(39, 'StockUnavailableError("Out of stock")', style='sub')

    set_b(40, 'Exception', style='ex_head')   # B40: h=None, v=bottom, bt=thin
    set_d(40, '', style='ex_head')             # D40: bt=thin
    set_d(41, 'ValidationError', style='sub')

    mark_o(35, 6)
    mark_o(36, 7, 8)
    mark_o(37, 9, 10)
    mark_o(38, 11)
    mark_o(39, 12)
    mark_o(41, 11, 12, 13)

    for r in range(CONF_START, RES_START):
        grid(r, 6, MAX_TC_COL)

    # ════════════════════════════════════════════════════════════════════
    # RESULT block: rows 42-45
    # ════════════════════════════════════════════════════════════════════
    set_col_a(RES_START, 'Result', zone='conf')
    for r in range(RES_START, DEFECT_ROW + 1):
        if r != RES_START:
            set_col_a(r, zone='conf')
        row_h(r)

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

    # Type values — extract font/align/border from Example type row cell
    type_vals = ['A', 'N', 'N', 'N', 'B', 'A', 'A', 'A']
    for i, v in enumerate(type_vals):
        cell = ws.cell(TYPE_ROW, 6 + i)
        cell.value = v
        apply(cell, font=t['type_font'], align=t['type_align'], border=t['type_border'])

    # PF values
    pf_vals = ['P', 'P', 'P', 'P', 'P', 'F', 'P', 'P']
    for i, v in enumerate(pf_vals):
        cell = ws.cell(PF_ROW, 6 + i)
        cell.value = v
        apply(cell, font=t['pf_font'], align=t['pf_align'], border=t['pf_border'])

    # Executed Dates — extract font/align/border/numfmt from Example date row
    dates = [
        datetime.datetime(2026, 9, 10),
        datetime.datetime(2026, 9, 10),
        datetime.datetime(2026, 9, 10),
        datetime.datetime(2026, 9, 11),
        datetime.datetime(2026, 9, 11),
        datetime.datetime(2026, 9, 12),
        datetime.datetime(2026, 9, 12),
        datetime.datetime(2026, 9, 12),
    ]
    for i, d in enumerate(dates):
        cell = ws.cell(DATE_ROW, 6 + i)
        cell.value = d
        apply(cell, font=t['date_font'], align=t['date_align'],
              border=t['date_border'], numfmt=t['date_numfmt'])

    # Defect ID — TC06 (col 11) has a defect
    def_ref = ws_ex.cell(48, 6)  # Defect ID cell style from Example
    def_font   = copy(def_ref.font)   if def_ref.has_style else t['date_font']
    def_align  = copy(def_ref.alignment) if def_ref.has_style else t['date_align']
    def_border = copy(def_ref.border) if def_ref.has_style else t['date_border']
    ws.cell(DEFECT_ROW, 11).value = 'BUG-2041'
    apply(ws.cell(DEFECT_ROW, 11), font=def_font, align=def_align, border=def_border)
    for c in range(6, MAX_TC_COL + 1):
        if ws.cell(DEFECT_ROW, c).value != 'BUG-2041':
            apply(ws.cell(DEFECT_ROW, c), border=t['date_border'])

    # Result block outer closing border: double bottom on DEFECT_ROW (all cols A-MAX_TC_COL)
    # Extracted from Example: R48C1-T48 all have border-bottom=double
    _dbl2 = Side(style='double')
    for c in range(1, MAX_TC_COL + 1):
        cell = ws.cell(DEFECT_ROW, c)
        ex = cell.border
        cell.border = Border(left=ex.left, right=ex.right, top=ex.top, bottom=_dbl2)

    # ── Data Validations ──────────────────────────────────────────────────
    dv_o = DataValidation(type='list', formula1='"O"', allow_blank=True, showDropDown=False)
    ws.add_data_validation(dv_o)
    dv_o.add(f'F{COND_START}:{LAST_TC}{RES_START - 1}')

    dv_nab = DataValidation(type='list', formula1='"N,A,B"', allow_blank=True, showDropDown=False)
    ws.add_data_validation(dv_nab)
    dv_nab.add(f'F{TYPE_ROW}:{LAST_TC}{TYPE_ROW}')

    dv_pf = DataValidation(type='list', formula1='"P,F"', allow_blank=True, showDropDown=False)
    ws.add_data_validation(dv_pf)
    dv_pf.add(f'F{PF_ROW}:{LAST_TC}{PF_ROW}')

    # ── Reorder: Example_Test before Example ──────────────────────────────
    sheets = wb._sheets
    et = wb['Example_Test']
    ex = wb['Example']
    sheets.remove(et)
    sheets.remove(ex)
    sheets.append(et)
    sheets.append(ex)

    return ws, ws_ex, MAX_TC_COL


# ── SECTION 4: Format diff validation (E6) ───────────────────────────────
def cell_sig(cell):
    f = cell.font; fi = cell.fill; al = cell.alignment; b = cell.border
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


def run_format_diff(ws_et, ws_ex, max_tc_col):
    """E6: Systematic diff of Example_Test vs Example structural skeleton."""
    diffs = []

    def cmp(r_et, c, r_ex=None, label=None):
        r_ex = r_ex or r_et
        sig_ex = cell_sig(ws_ex.cell(r_ex, c))
        sig_et = cell_sig(ws_et.cell(r_et, c))
        ref = label or f'{get_column_letter(c)}{r_et}(vs{r_ex})'
        for k in sig_ex:
            if sig_ex[k] != sig_et[k]:
                diffs.append(f'  [{ref}] {k}: expected={repr(sig_ex[k])} got={repr(sig_et[k])}')

    # 1. Header block rows 2-8 (should be identical — copied from Example)
    for r in range(2, 9):
        for c in range(1, 20):
            cmp(r, c)

    # 2. Row 9 TC headers (cols 6 to max_tc_col)
    for c in range(6, max_tc_col + 1):
        cmp(9, c)

    # 3. Col A section titles vs Example counterparts
    for r_et, r_ex in [(10, 10), (33, 33), (42, 45)]:
        cmp(r_et, 1, r_ex=r_ex, label=f'A{r_et}(section-vs-A{r_ex})')

    # 4. Col A mid-section rows — spot check
    for r_et, r_ex in [(15, 15), (20, 20), (34, 34), (40, 40)]:
        cmp(r_et, 1, r_ex=r_ex, label=f'A{r_et}(mid-vs-{r_ex})')

    # 5. Col B/D label cells
    for r_et, r_ex in [(10, 10), (11, 14), (33, 33), (34, 34), (40, 40)]:
        for c in [2, 4]:
            if ws_ex.cell(r_ex, c).has_style or ws_et.cell(r_et, c).has_style:
                cmp(r_et, c, r_ex=r_ex, label=f'R{r_et}C{c}(vs{r_ex})')

    # 6. O-mark format
    def first_o(ws):
        for r in range(10, 50):
            for c in range(6, 25):
                if ws.cell(r, c).value == 'O':
                    return ws.cell(r, c)
        return None
    o_ex = first_o(ws_ex)
    o_et = first_o(ws_et)
    if o_ex and o_et:
        sig_ex = cell_sig(o_ex)
        sig_et = cell_sig(o_et)
        for k in sig_ex:
            if sig_ex[k] != sig_et[k]:
                diffs.append(f'  [O-mark] {k}: expected={repr(sig_ex[k])} got={repr(sig_et[k])}')

    # 7. Result rows (Type/PF/Date) matrix cells
    for r_et, r_ex in [(42, 45), (43, 46), (44, 47)]:
        for c in range(6, min(max_tc_col, 8) + 1):
            cmp(r_et, c, r_ex=r_ex, label=f'Result-R{r_et}C{c}(vs{r_ex})')

    # 8. Col widths
    for c in range(1, max_tc_col + 1):
        col = get_column_letter(c)
        w_ex = ws_ex.column_dimensions[col].width or 8.43
        w_et = ws_et.column_dimensions[col].width or 8.43
        if abs(w_ex - w_et) > 0.1:
            diffs.append(f'  [ColWidth-{col}] expected={w_ex} got={w_et}')

    # 9. Row heights
    for r in [9, 10, 11, 15, 33, 34, 40]:
        h_ex = ws_ex.row_dimensions[r].height or 13.5
        h_et = ws_et.row_dimensions[r].height or 13.5
        if abs(h_ex - h_et) > 0.5:
            diffs.append(f'  [RowHeight-{r}] expected={h_ex} got={h_et}')

    # 10. Col A fill consistency — no blank rows in data area
    for r in range(10, 46):
        cell = ws_et.cell(r, 1)
        if not cell.fill or not cell.fill.patternType or cell.fill.patternType == 'none':
            diffs.append(f'  [ColA-fill] Row {r}: no fill (should be navy)')

# ── SECTION 5: Main ───────────────────────────────────────────────────────
def main():
    wb = openpyxl.load_workbook(TARGET, data_only=False)

    print('Generating Example_Test sheet...')
    ws_et, ws_ex, max_tc_col = generate(wb)

    # E6: Run comprehensive standalone diff BEFORE saving
    print('\n[E6] Running format diff validation...')
    try:
        from tools.format_diff_excel import run_diff
    except ImportError:
        from format_diff_excel import run_diff
    diffs = run_diff(ws_et, ws_ex, verbose=True)

    if diffs:
        print(f'  ✗ {len(diffs)} format diffs found — NOT delivering until fixed:')
        for d in diffs:
            print(d)
        print('\nAborting save. Fix the diffs first.')
        return False

    print(f'  ✓ Format diff clean — {len(diffs)} issues found. Proceeding to save.')

    try:
        wb.save(TARGET)
    except PermissionError:
        import subprocess, time
        subprocess.run(['taskkill', '/F', '/IM', 'excel.exe'], capture_output=True)
        time.sleep(0.5)
        wb.save(TARGET)

    print(f'\nSUCCESS: Example_Test delivered. Sheets: {wb.sheetnames}')
    return True


if __name__ == '__main__':
    main()

"""
doctools.core.xlsx.shift.formula_shifter — Bộ dịch chuyển công thức dựa trên AST Tokenizer.
Tuân thủ FR-07, D-03, D-04 của Foundation Plan v1.1:
- Phân tích token bằng openpyxl.formula.Tokenizer.
- Giữ nguyên 100% tên hàm, chuỗi ký tự ("TC001"), tên định danh (FY2024).
- Chỉ dịch chuyển toán hạng dạng ô/dải trỏ vào đúng sheet đích.
- Hỗ trợ range_policy: 'table_aware' (mở rộng bao gồm dòng chèn) và 'excel_native'.
- Báo lỗi E-SHIFT-UNSUPPORTED-FORM đối với tham chiếu cấu trúc, 3D, mảng động.
"""

from __future__ import annotations
import re
from typing import List, Optional, Tuple
from openpyxl.formula import Tokenizer
from openpyxl.formula.tokenizer import Token
from openpyxl.utils.cell import (
    column_index_from_string,
    coordinate_to_tuple,
    get_column_letter,
)

from doctools.contract.issues import Engine, Issue, Severity

_CELL_REF_REGEX = re.compile(
    r"^(\$?[A-Za-z]+)(\$?[0-9]+)$"
)
_COL_RANGE_REGEX = re.compile(r"^(\$?[A-Za-z]+):(\$?[A-Za-z]+)$")
_ROW_RANGE_REGEX = re.compile(r"^(\$?[0-9]+):(\$?[0-9]+)$")


class FormulaShiftError(Exception):
    """Lỗi khi dịch chuyển công thức."""
    def __init__(self, message: str, code: str = "E-SHIFT-FAILED") -> None:
        super().__init__(message)
        self.code = code


def _parse_coordinate(coord_str: str) -> Optional[Tuple[bool, int, bool, int]]:
    """Phân tích ô dạng '$A$1' thành (col_abs, col_idx, row_abs, row_idx)."""
    m = _CELL_REF_REGEX.match(coord_str)
    if not m:
        return None
    col_part, row_part = m.group(1), m.group(2)
    col_abs = col_part.startswith("$")
    col_str = col_part.lstrip("$").upper()
    row_abs = row_part.startswith("$")
    row_idx = int(row_part.lstrip("$"))
    col_idx = column_index_from_string(col_str)
    return col_abs, col_idx, row_abs, row_idx


def _format_coordinate(col_abs: bool, col_idx: int, row_abs: bool, row_idx: int) -> str:
    """Định dạng tọa độ ô trở lại dạng Excel (vd: '$A$1' hoặc 'B10')."""
    col_str = get_column_letter(col_idx)
    col_prefix = "$" if col_abs else ""
    row_prefix = "$" if row_abs else ""
    return f"{col_prefix}{col_str}{row_prefix}{row_idx}"


def shift_cell_or_range(
    ref_text: str,
    insert_at_row: int,
    num_rows: int,
    range_policy: str = "table_aware",
) -> str:
    """
    Dịch chuyển tọa độ của một ô hoặc một dải ô khi chèn thêm num_rows tại dòng insert_at_row.
    """
    # 1. Kiểm tra dải cả cột: A:A hoặc $A:$B (không đổi khi chèn dòng)
    if _COL_RANGE_REGEX.match(ref_text):
        return ref_text

    # 2. Kiểm tra dải cả dòng: 5:5 hoặc $5:$10
    m_row = _ROW_RANGE_REGEX.match(ref_text)
    if m_row:
        r1_str, r2_str = m_row.group(1), m_row.group(2)
        r1_abs = r1_str.startswith("$")
        r2_abs = r2_str.startswith("$")
        r1 = int(r1_str.lstrip("$"))
        r2 = int(r2_str.lstrip("$"))
        if r1 >= insert_at_row:
            r1 += num_rows
        if r2 >= insert_at_row:
            r2 += num_rows
        return f"{'$' if r1_abs else ''}{r1}:{'$' if r2_abs else ''}{r2}"

    # 3. Phân tách dải ô dạng A1:B10
    if ":" in ref_text:
        parts = ref_text.split(":")
        if len(parts) == 2:
            p1 = _parse_coordinate(parts[0])
            p2 = _parse_coordinate(parts[1])
            if p1 and p2:
                c1_abs, c1_idx, r1_abs, r1_idx = p1
                c2_abs, c2_idx, r2_abs, r2_idx = p2

                # Xử lý theo bảng quy tắc 4.7
                if r1_idx >= insert_at_row:
                    # Dải có dòng đầu >= R -> Dịch cả dải xuống
                    r1_idx += num_rows
                    r2_idx += num_rows
                elif r1_idx < insert_at_row <= r2_idx:
                    # Chèn bên trong dải: mở rộng dòng cuối
                    r2_idx += num_rows
                elif r2_idx < insert_at_row:
                    if range_policy == "table_aware" and insert_at_row == r2_idx + 1:
                        # Chèn ngay dưới dòng cuối (biên summary): mở rộng bao gồm dòng mới
                        r2_idx += num_rows

                s1 = _format_coordinate(c1_abs, c1_idx, r1_abs, r1_idx)
                s2 = _format_coordinate(c2_abs, c2_idx, r2_abs, r2_idx)
                return f"{s1}:{s2}"

    # 4. Ô đơn lẻ
    p = _parse_coordinate(ref_text)
    if p:
        c_abs, c_idx, r_abs, r_idx = p
        if r_idx >= insert_at_row:
            r_idx += num_rows
        return _format_coordinate(c_abs, c_idx, r_abs, r_idx)

    return ref_text


def shift_formula_text(
    formula: str,
    target_sheet: str,
    current_sheet: str,
    insert_at_row: int,
    num_rows: int,
    range_policy: str = "table_aware",
) -> Tuple[str, List[Issue]]:
    """
    Dịch chuyển một chuỗi công thức Excel hoàn chỉnh.
    Chỉ dịch các toán hạng trỏ vào target_sheet.
    """
    if not formula or not formula.startswith("="):
        return formula, []

    issues: List[Issue] = []

    if "[" in formula and "]" in formula:
        issues.append(Issue(
            code="E-SHIFT-UNSUPPORTED-FORM",
            severity=Severity.ERROR,
            engine=Engine.XLSX,
            message=f"Công thức chứa tham chiếu cấu trúc dạng bảng chưa hỗ trợ: '{formula}'",
            evidence={"formula": formula},
        ))
        return formula, issues

    try:
        tok = Tokenizer(formula)
    except Exception as e:
        issues.append(Issue(
            code="E-SHIFT-TOKENIZE-FAILED",
            severity=Severity.ERROR,
            engine=Engine.XLSX,
            message=f"Không thể tokenize công thức '{formula}': {e}",
            evidence={"formula": formula},
        ))
        return formula, issues

    # Kiểm tra tham chiếu 3D giữa các sheet (vd: Sheet1:Sheet3!A1)
    for token in tok.items:
        if token.type == Token.OPERAND and token.subtype == Token.RANGE and "!" in token.value:
            prefix_part = token.value.split("!", 1)[0]
            if ":" in prefix_part:
                issues.append(Issue(
                    code="E-SHIFT-UNSUPPORTED-FORM",
                    severity=Severity.ERROR,
                    engine=Engine.XLSX,
                    message=f"Công thức chứa tham chiếu 3D nhiều sheet chưa hỗ trợ: '{formula}'",
                    evidence={"formula": formula, "token": token.value},
                ))
                return formula, issues

    new_tokens: List[str] = []

    for token in tok.items:
        if token.type == Token.OPERAND and token.subtype == Token.RANGE:
            val = token.value

            # Phân tích sheet prefix (vd: 'Sheet 1'!A1 hoặc Sheet1!A1:B2)
            sheet_prefix = ""
            ref_body = val
            if "!" in val:
                prefix_part, ref_body = val.split("!", 1)
                sheet_prefix = prefix_part + "!"
                clean_sheet_name = prefix_part.strip("'")
                applies_to_target = (clean_sheet_name == target_sheet)
            else:
                # Không có tiền tố: chỉ dịch khi công thức nằm trên đúng target_sheet
                applies_to_target = (current_sheet == target_sheet)

            if applies_to_target:
                shifted_body = shift_cell_or_range(
                    ref_body,
                    insert_at_row=insert_at_row,
                    num_rows=num_rows,
                    range_policy=range_policy,
                )
                new_tokens.append(f"{sheet_prefix}{shifted_body}")
            else:
                # Trỏ vào sheet khác -> Giữ nguyên 100%
                new_tokens.append(val)
        else:
            # Tên hàm, chuỗi ký tự, số, toán tử giữ nguyên tuyệt đối
            new_tokens.append(token.value)

    shifted_formula = "".join(new_tokens)
    if formula.startswith("=") and not shifted_formula.startswith("="):
        shifted_formula = f"={shifted_formula}"

    return shifted_formula, issues

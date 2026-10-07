"""
doctools.core.xlsx.shift.shift_manager — Quản lý dịch chuyển đồng bộ toàn bộ bảng tính.
Tuân thủ FR-07, TC-01..TC-06 của Foundation Plan v1.1:
- Dịch chuyển mọi đối tượng phụ thuộc vị trí trong cùng một lần.
- Dịch công thức trên mọi sheet (bao gồm cả công thức hai chiều giữa các sheet).
- Dịch và mở rộng merged cells an toàn.
- Dịch thuộc tính chiều cao dòng (row_dimensions).
- Dịch phạm vi tên đã định nghĩa (defined names).
"""

from __future__ import annotations
from typing import List, Tuple
import openpyxl
from openpyxl.worksheet.cell_range import CellRange

from doctools.contract.issues import Engine, Issue, Severity
from .formula_shifter import shift_formula_text


class ShiftManager:
    """Bộ điều phối dịch chuyển toàn diện cho Workbook Excel."""

    def __init__(self, workbook: openpyxl.Workbook) -> None:
        self.workbook = workbook

    def shift_sheet_rows(
        self,
        sheet_name: str,
        insert_at_row: int,
        num_rows: int,
        range_policy: str = "table_aware",
    ) -> List[Issue]:
        """
        Dịch chuyển toàn bộ đối tượng phụ thuộc khi chèn thêm num_rows tại dòng insert_at_row trên sheet_name.
        """
        issues: List[Issue] = []

        if sheet_name not in self.workbook.sheetnames:
            issues.append(Issue(
                code="E-SHIFT-SHEET-NOT-FOUND",
                severity=Severity.ERROR,
                engine=Engine.XLSX,
                message=f"Sheet '{sheet_name}' không tồn tại trong workbook.",
            ))
            return issues

        # 1. Dịch chuyển Merged Cells trên sheet đích
        ws = self.workbook[sheet_name]
        new_merged_ranges: List[CellRange] = []
        old_ranges = list(ws.merged_cells.ranges)

        for rng in old_ranges:
            min_col, min_row, max_col, max_row = rng.bounds
            if min_row >= insert_at_row:
                # Toàn bộ khối merge nằm sau điểm chèn: dịch xuống
                new_bounds = (min_col, min_row + num_rows, max_col, max_row + num_rows)
                new_merged_ranges.append(CellRange(min_col=new_bounds[0], min_row=new_bounds[1],
                                                   max_col=new_bounds[2], max_row=new_bounds[3]))
            elif min_row < insert_at_row <= max_row:
                # Điểm chèn nằm giữa khối merge: mở rộng khối
                new_bounds = (min_col, min_row, max_col, max_row + num_rows)
                new_merged_ranges.append(CellRange(min_col=new_bounds[0], min_row=new_bounds[1],
                                                   max_col=new_bounds[2], max_row=new_bounds[3]))
            else:
                new_merged_ranges.append(rng)

        # Xóa các range cũ và gán range mới
        ws.merged_cells.ranges.clear()
        for nr in new_merged_ranges:
            ws.merged_cells.add(nr)

        # 2. Dịch chuyển chiều cao dòng (row_dimensions)
        existing_dims = list(ws.row_dimensions.items())
        new_dims = {}
        for r_idx, dim in existing_dims:
            if r_idx >= insert_at_row:
                new_dims[r_idx + num_rows] = dim.height
            else:
                new_dims[r_idx] = dim.height

        for r_idx, h in new_dims.items():
            if h is not None:
                ws.row_dimensions[r_idx].height = h

        # 3. Dịch chuyển công thức trên TOÀN BỘ các sheet trong Workbook
        for s_name in self.workbook.sheetnames:
            cur_ws = self.workbook[s_name]
            max_r = cur_ws.max_row or 0
            max_c = cur_ws.max_column or 0

            # Nếu chính là sheet đích thì cần quét các ô trước khi dời dữ liệu dòng
            # Lưu ý: ô có dòng >= insert_at_row trên sheet đích sẽ được dời giá trị khi chèn dòng
            for r in range(1, max_r + 1):
                for c in range(1, max_c + 1):
                    cell = cur_ws.cell(row=r, column=c)
                    val = cell.value
                    if isinstance(val, str) and val.startswith("="):
                        shifted_val, form_issues = shift_formula_text(
                            formula=val,
                            target_sheet=sheet_name,
                            current_sheet=s_name,
                            insert_at_row=insert_at_row,
                            num_rows=num_rows,
                            range_policy=range_policy,
                        )
                        issues.extend(form_issues)
                        cell.value = shifted_val

        # 4. Dịch chuyển Defined Names
        for name_obj in list(self.workbook.defined_names.values()):
            if hasattr(name_obj, "value") and name_obj.value:
                val = name_obj.value
                if isinstance(val, str) and "=" in val:
                    formula_str = val if val.startswith("=") else f"={val}"
                    shifted_val, name_issues = shift_formula_text(
                        formula=formula_str,
                        target_sheet=sheet_name,
                        current_sheet=sheet_name,
                        insert_at_row=insert_at_row,
                        num_rows=num_rows,
                        range_policy=range_policy,
                    )
                    issues.extend(name_issues)
                    name_obj.value = shifted_val.lstrip("=")

        return issues

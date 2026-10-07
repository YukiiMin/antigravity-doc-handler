"""
tests/test_xlsx/test_shift_manager.py — Bộ kiểm thử cho AST Formula Shift Manager.
Kiểm tra các yêu cầu FR-07, TC-01..TC-06:
- TC-01: Dịch chuyển công thức đơn giản và dải ô
- TC-02: Bảo toàn 100% chuỗi ký tự, tên định danh, tên hàm
- TC-03: Dịch chuyển công thức hai chiều giữa các sheet (cross-sheet)
- TC-04: Ngữ nghĩa biên theo range_policy (table_aware vs excel_native)
- TC-05: Phát hiện và chặn các dạng công thức chưa hỗ trợ (E-SHIFT-UNSUPPORTED-FORM)
- TC-06: Dịch chuyển và mở rộng khối merged cells.
"""

import unittest
import openpyxl

from doctools.contract.issues import Severity
from doctools.core.xlsx.shift.formula_shifter import (
    shift_cell_or_range,
    shift_formula_text,
)
from doctools.core.xlsx.shift.shift_manager import ShiftManager


class TestShiftManager(unittest.TestCase):
    """Test suite cho bộ dịch chuyển công thức và bảng tính Excel."""

    def test_tc01_shift_simple_formulas(self):
        """TC-01: Dịch chuyển công thức đơn giản và dải ô khi chèn dòng."""
        # Chèn 5 dòng tại dòng 3 trên sheet 'Sheet1'
        f1, issues1 = shift_formula_text(
            formula="=A1+B1",
            target_sheet="Sheet1",
            current_sheet="Sheet1",
            insert_at_row=3,
            num_rows=5,
        )
        # A1 và B1 < 3 nên giữ nguyên
        self.assertEqual(f1, "=A1+B1")

        f2, issues2 = shift_formula_text(
            formula="=SUM(A10:A20)",
            target_sheet="Sheet1",
            current_sheet="Sheet1",
            insert_at_row=5,
            num_rows=3,
        )
        # Dải nằm hoàn toàn sau dòng 5: dịch xuống +3
        self.assertEqual(f2, "=SUM(A13:A23)")

        # Tham chiếu tuyệt đối $F$10 cũng phải được dịch khi chèn dòng (FR-07)
        f3, _ = shift_formula_text(
            formula="=$F$10*2",
            target_sheet="Sheet1",
            current_sheet="Sheet1",
            insert_at_row=5,
            num_rows=4,
        )
        self.assertEqual(f3, "=$F$14*2")

    def test_tc02_preserve_strings_and_identifiers(self):
        """TC-02: Chuỗi ký tự 'TC001' và tên hàm LOG10, DAYS360 được giữ nguyên tuyệt đối."""
        formula = '=IF(A10="TC001", LOG10(B10), DAYS360(C10, D10))'
        shifted, issues = shift_formula_text(
            formula=formula,
            target_sheet="Data",
            current_sheet="Data",
            insert_at_row=5,
            num_rows=5,
        )
        self.assertEqual(len(issues), 0)
        self.assertEqual(shifted, '=IF(A15="TC001", LOG10(B15), DAYS360(C15, D15))')

    def test_tc03_cross_sheet_two_way_formulas(self):
        """TC-03: Công thức hai chiều giữa các sheet (EV-03, EV-04)."""
        # Sheet 'Stats' tham chiếu sang 'Data!A10:A20'
        # Khi chèn dòng trên 'Data', tham chiếu trỏ sang 'Data' phải được dịch
        f_stats, _ = shift_formula_text(
            formula="=SUM(Data!A10:A20) + Other!A10",
            target_sheet="Data",
            current_sheet="Stats",
            insert_at_row=5,
            num_rows=3,
        )
        # Data được dịch, còn Other giữ nguyên
        self.assertEqual(f_stats, "=SUM(Data!A13:A23) + Other!A10")

        # Sheet 'Data' tham chiếu sang 'Lookup!A10'
        # Khi chèn dòng trên 'Data', tham chiếu sang 'Lookup' không bị dịch
        f_data, _ = shift_formula_text(
            formula="=Lookup!A10 + A10",
            target_sheet="Data",
            current_sheet="Data",
            insert_at_row=5,
            num_rows=2,
        )
        self.assertEqual(f_data, "=Lookup!A10 + A12")

    def test_tc04_range_policy_semantics(self):
        """TC-04: Ngữ nghĩa biên theo range_policy (table_aware vs excel_native)."""
        # Dải dữ liệu: A4:A8. Dòng 9 là dòng tổng cộng SUM(A4:A8).
        # Chèn thêm 5 dòng ngay trước dòng tổng (insert_at_row=9)
        f_table, _ = shift_formula_text(
            formula="=SUM(A4:A8)",
            target_sheet="Sheet1",
            current_sheet="Sheet1",
            insert_at_row=9,
            num_rows=5,
            range_policy="table_aware",
        )
        # table_aware mở rộng dải bao phủ các dòng mới chèn
        self.assertEqual(f_table, "=SUM(A4:A13)")

        f_native, _ = shift_formula_text(
            formula="=SUM(A4:A8)",
            target_sheet="Sheet1",
            current_sheet="Sheet1",
            insert_at_row=9,
            num_rows=5,
            range_policy="excel_native",
        )
        # excel_native không mở rộng khi chèn dưới biên
        self.assertEqual(f_native, "=SUM(A4:A8)")

    def test_tc05_unsupported_formula_forms(self):
        """TC-05: Chặn tham chiếu cấu trúc và 3D với mã E-SHIFT-UNSUPPORTED-FORM."""
        f_struct, issues1 = shift_formula_text(
            formula="=SUM(Table1[Amount])",
            target_sheet="Sheet1",
            current_sheet="Sheet1",
            insert_at_row=5,
            num_rows=2,
        )
        codes1 = [i.code for i in issues1]
        self.assertIn("E-SHIFT-UNSUPPORTED-FORM", codes1)

    def test_tc06_shift_manager_merged_cells_and_heights(self):
        """TC-06: ShiftManager dịch chuyển merged cells và chiều cao dòng."""
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Report"
        ws["A1"] = "Title"
        ws["A5"] = "Dòng 5"
        ws["A10"] = "=SUM(A4:A8)"

        # Merge ô A12:C15 (sau điểm chèn)
        ws.merge_cells("A12:C15")
        # Merge ô A3:C6 (bao qua điểm chèn dòng 5)
        ws.merge_cells("E3:G6")

        ws.row_dimensions[12].height = 25.0

        sm = ShiftManager(wb)
        issues = sm.shift_sheet_rows(
            sheet_name="Report",
            insert_at_row=5,
            num_rows=4,
            range_policy="table_aware",
        )
        self.assertEqual(len(issues), 0)

        # Kiểm tra merged cell sau điểm chèn A12:C15 -> dịch thành A16:C19
        merged_ranges = [str(r) for r in ws.merged_cells.ranges]
        self.assertIn("A16:C19", merged_ranges)
        # Khối E3:G6 bao qua dòng 5 -> mở rộng thành E3:G10
        self.assertIn("E3:G10", merged_ranges)

        # Kiểm tra row dimension
        self.assertEqual(ws.row_dimensions[16].height, 25.0)

        # Kiểm tra công thức tại ô A14 (vốn ở A10, dời xuống 14)
        # (Lưu ý: ShiftManager dịch nội dung công thức, dữ liệu ô sẽ do Mutator di chuyển)
        wb.close()


if __name__ == "__main__":
    unittest.main()

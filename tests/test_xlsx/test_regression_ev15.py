"""
tests.test_xlsx.test_regression_ev15 — Bộ test hồi quy khóa chặt 3 lỗi thật phát hiện từ EV-15.
Tuân thủ EV-15, TC-59, TC-60, TC-61 của Execution Slice (Phase 2.4.1):
- TC-59: openpyxl.copy_worksheet() làm rơi sạch DataValidation khi clone sheet.
- TC-60: Bảng Statistics bị khuyết viền hair ở các dòng dữ liệu dưới (W-XLSX-BORDER-GAP).
- TC-61: Sheet mẫu Return(Staff) tham chiếu ô rỗng -AA7 (W-FORMULA-EMPTY-CELL-REF).
"""

import unittest
import openpyxl
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.styles import Border, Side

from doctools.core.xlsx.inspect.format_profiler import FormatProfiler
from doctools.core.xlsx.inspect.formula_profiler import FormulaProfiler


class TestRegressionEV15(unittest.TestCase):
    """Bộ test hồi quy tái hiện và kiểm soát 3 lỗi thực nghiệm EV-15."""

    def test_tc59_reproduce_openpyxl_copy_worksheet_drops_data_validations(self):
        """
        TC-59 (Vulnerability Reproduction):
        Chứng minh openpyxl.copy_worksheet() làm rơi sạch DataValidation.
        Khi nhân bản sheet Example có dropdown 'O' hoặc 'N/A', sheet con bị rỗng validation.
        """
        wb = openpyxl.Workbook()
        ws_src = wb.active
        ws_src.title = "Example"

        # Thiết lập DataValidation (List O/X) trên cột C (C3:C10)
        dv = DataValidation(type="list", formula1='"O,X,N/A"', allow_blank=True)
        ws_src.add_data_validation(dv)
        dv.add("C3:C10")

        # Xác nhận sheet gốc có 1 DataValidation
        self.assertEqual(len(ws_src.data_validations), 1)

        # Sử dụng API mặc định của openpyxl để clone sheet
        ws_copy = wb.copy_worksheet(ws_src)
        ws_copy.title = "Handover (Staff)"

        # BẰNG CHỨNG THỰC NGHIỆM EV-15.1:
        # openpyxl.copy_worksheet làm rơi sạch data_validations!
        self.assertEqual(
            len(ws_copy.data_validations),
            0,
            "openpyxl.copy_worksheet đã làm rơi toàn bộ Data Validation của sheet nguồn!",
        )

    def test_tc60_detect_broken_hair_borders_on_statistics_table(self):
        """
        TC-60 (Hair Border Gap Detection):
        Tái hiện cấu trúc bảng Statistics: dòng 12 có đủ viền hair 4 phía,
        các dòng 13..15 bị đứt gãy viền (chỉ có top/bottom, khuyết left/right).
        FormatProfiler phải phát hiện và cảnh báo W-XLSX-BORDER-GAP.
        """
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Statistics"

        hair_side = Side(border_style="hair", color="000000")
        full_hair = Border(top=hair_side, bottom=hair_side, left=hair_side, right=hair_side)
        broken_hair = Border(top=hair_side, bottom=hair_side)  # Khuyết left và right!

        # Dòng 1..5: Dòng mẫu prototype row có đủ viền hair
        for row in range(1, 5):
            for col in range(2, 5):  # Cột B, C, D
                ws.cell(row=row, column=col, value=f"Header {col}").border = full_hair

        # Dòng 6..10: Bị mất sạch viền bên trong khối dữ liệu (như dòng 19..21 của Statistics)
        for row in range(6, 11):
            for col in range(2, 5):
                ws.cell(row=row, column=col, value=100)  # Mặc định không có viền (border gap!)

        # Dùng FormatProfiler để quét định dạng
        profiler = FormatProfiler(wb)
        report = profiler.profile(target_sheet="Statistics")

        gaps = report.get("border_gaps_detected", [])
        self.assertGreaterEqual(len(gaps), 1)
        self.assertEqual(gaps[0]["code"], "W-XLSX-BORDER-GAP")
        self.assertEqual(gaps[0]["sheet"], "Statistics")

    def test_tc61_detect_empty_cell_subtraction_anomaly(self):
        """
        TC-61 (Empty Cell Reference Anomaly Detection):
        Tái hiện lỗi sheet Return(Staff) trong dataset Report5:
        Ô Q7 chứa tổng số test cases (22).
        Ô AA7 là ô hoàn toàn rỗng.
        Ô O8 gõ nhầm công thức =Q7-AA7 thay vì =Q7-O7.
        FormulaProfiler phải phát hiện và cảnh báo W-FORMULA-EMPTY-CELL-REF.
        """
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Return(Staff)"

        # Điền dữ liệu
        ws["Q7"] = 22
        # AA7 cố tình để rỗng (value=None)
        self.assertIsNone(ws["AA7"].value)

        # Đặt công thức có lỗi tham chiếu ô rỗng
        ws["O8"] = "=Q7-AA7"

        # Phân tích công thức bằng FormulaProfiler
        profiler = FormulaProfiler(wb)
        report = profiler.profile(target_sheet="Return(Staff)")

        empty_refs = report.get("empty_cell_references", [])
        self.assertGreaterEqual(
            len(empty_refs),
            1,
            "FormulaProfiler phải phát hiện cảnh báo W-FORMULA-EMPTY-CELL-REF",
        )
        found_aa7 = any("AA7" in er["target"] for er in empty_refs)
        self.assertTrue(found_aa7, "Phải phát hiện tham chiếu tới ô rỗng AA7")
        self.assertEqual(empty_refs[0]["code"], "W-FORMULA-EMPTY-CELL-REF")


if __name__ == "__main__":
    unittest.main()

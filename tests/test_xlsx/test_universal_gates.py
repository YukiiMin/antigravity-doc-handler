"""
Unit test suite for doctools.gates.xlsx (13 Universal Gates & Structural Diff).
Kiểm thử toàn diện Tiểu bước 2.1.5:
- UG-01 DrawingML Preservation Gate
- UG-02 Formula Syntax Gate & UG-03 Ref Error Gate
- UG-04 Merged Border Gate
- UG-12 Package Integrity Gate
- XlsxStructuralDiffer (phát hiện hồi quy #REF!, bớt sheet, delta công thức)
- Tích hợp ToolRegistry MCP: xlsx.validate, xlsx.diff, xlsx.inspect
"""

import io
import os
import shutil
import tempfile
import unittest
import zipfile
import openpyxl
from openpyxl.styles import Border, Side

from doctools.contract.issues import Severity
from doctools.gates.xlsx.structural_diff import XlsxStructuralDiffer
from doctools.gates.xlsx.universal_gates import XlsxUniversalGates
from doctools.infra.file_store import FileStore
from doctools.operations.xlsx.inspect_ops import register_xlsx_inspect_tools
from doctools.operations.xlsx.validate_ops import register_xlsx_validate_tools
from doctools.registry import ToolRegistry


class TestUniversalGates(unittest.TestCase):
    """Kiểm thử bộ cổng UG-01..UG-13 và đối soát cấu trúc."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.mkdtemp()
        self.file_store = FileStore(base_dir=os.path.join(self.temp_dir, "filestore"))
        self.gates = XlsxUniversalGates()

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_ug02_ug03_formula_errors_and_syntax(self) -> None:
        """Kiểm tra bắt lỗi cú pháp công thức (UG-02) và lỗi #REF!, #DIV/0! (UG-03)."""
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Formulas"

        # Lỗi ngoặc không cân bằng (UG-02)
        ws["A1"] = "=SUM(B1:B10"
        # Lỗi #REF! (UG-03 ERROR)
        ws["A2"] = "#REF!"
        # Lỗi #DIV/0! (UG-03 WARNING)
        ws["A3"] = "#DIV/0!"
        # Công thức hợp lệ
        ws["A4"] = "=SUM(B1:B10)"

        issues = self.gates.validate(wb)
        codes = [i.code for i in issues]

        self.assertIn("E-XLSX-UG02-SYNTAX-PAREN", codes)
        self.assertIn("E-XLSX-UG03-FORMULA-ERROR", codes)
        self.assertIn("W-XLSX-UG03-FORMULA-ERROR", codes)

    def test_ug04_merged_borders(self) -> None:
        """Kiểm tra phát hiện vùng gộp đứt đoạn viền đáy (UG-04)."""
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "MergedSheet"
        ws.merge_cells("A1:C2")

        # Đặt viền top-left có bottom style
        ws["A1"].border = Border(
            top=Side(style="thin"),
            bottom=Side(style="thin"),
            left=Side(style="thin"),
            right=Side(style="thin"),
        )
        # Ô C2 (bottom-right) không có border
        ws["C2"].border = Border()

        issues = self.gates.validate(wb)
        codes = [i.code for i in issues]
        self.assertIn("W-XLSX-UG04-BORDER-DISCONTINUITY", codes)

    def test_ug12_package_integrity(self) -> None:
        """Kiểm tra tính toàn vẹn gói OpenXML OPC (UG-12)."""
        # File không phải ZIP
        bad_bytes = b"NOT_A_VALID_ZIP_PACKAGE"
        issues = self.gates.validate(bad_bytes)
        self.assertTrue(any(i.code == "E-XLSX-UG12-BAD-ZIP" for i in issues))

        # ZIP thiếu [Content_Types].xml
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as z:
            z.writestr("xl/workbook.xml", "<workbook/>")
        issues2 = self.gates.validate(buf.getvalue())
        self.assertTrue(any(i.code == "E-XLSX-UG12-NO-CONTENT-TYPES" for i in issues2))

    def test_structural_diff(self) -> None:
        """Kiểm tra đối soát sai lệch giữa 2 workbook và phát hiện hồi quy #REF!."""
        wb1 = openpyxl.Workbook()
        ws1 = wb1.active
        ws1.title = "Main"
        ws1["A1"] = "=SUM(B1:B5)"
        ws1["A2"] = 100

        wb2 = openpyxl.Workbook()
        ws2_main = wb2.active
        ws2_main.title = "Main"
        ws2_main["A1"] = "=SUM(B1:B5)"
        ws2_main["A2"] = 200
        ws2_main["A3"] = "#REF!"  # Hồi quy lỗi #REF! mới xuất hiện

        ws2_extra = wb2.create_sheet("ExtraSheet")
        ws2_extra["B1"] = "=AVERAGE(C1:C10)"

        report, issues = XlsxStructuralDiffer.diff(wb1, wb2)

        self.assertIn("ExtraSheet", report.sheets_added)
        self.assertIn("Main", report.sheets_preserved)
        self.assertEqual(report.total_errors_mod, 1)
        self.assertEqual(report.total_errors_orig, 0)
        self.assertTrue(any(i.code == "E-XLSX-DIFF-REF-REGRESSION" for i in issues))

    def test_mcp_tools_validate_diff_inspect(self) -> None:
        """Kiểm tra tích hợp các công cụ MCP xlsx.validate, xlsx.diff và xlsx.inspect."""
        registry = ToolRegistry(file_store=self.file_store)
        register_xlsx_validate_tools(registry)
        register_xlsx_inspect_tools(registry)

        # Lưu 2 file mẫu
        path_a = os.path.join(self.temp_dir, "file_a.xlsx")
        path_b = os.path.join(self.temp_dir, "file_b.xlsx")

        wb_a = openpyxl.Workbook()
        wb_a.active.title = "SheetA"
        wb_a.active["A1"] = "=SUM(1, 2)"
        wb_a.save(path_a)

        wb_b = openpyxl.Workbook()
        wb_b.active.title = "SheetA"
        wb_b.active["A1"] = "=SUM(1, 2)"
        wb_b.active["A2"] = "=COUNT(B1:B5)"
        wb_b.save(path_b)

        # 1. xlsx.validate
        val_res = registry.execute("xlsx.validate", {"file_ref": path_a})
        self.assertTrue(val_res.success)
        self.assertIn("13_UNIVERSAL_GATES_VERIFIED", val_res.guarantees_applied)

        # 2. xlsx.diff
        diff_res = registry.execute("xlsx.diff", {"original_ref": path_a, "modified_ref": path_b})
        self.assertTrue(diff_res.success)
        self.assertIn("diff_report", diff_res.stats.extra)

        # 3. xlsx.inspect
        insp_res = registry.execute("xlsx.inspect", {"file_ref": path_b})
        self.assertTrue(insp_res.success)
        self.assertEqual(insp_res.stats.extra["total_formulas"], 2)
        self.assertIn("SUM", insp_res.stats.extra["unique_functions"])
        self.assertIn("COUNT", insp_res.stats.extra["unique_functions"])


if __name__ == "__main__":
    unittest.main()

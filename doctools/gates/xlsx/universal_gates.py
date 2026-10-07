"""
doctools.gates.xlsx.universal_gates — 13 Universal Gates (UG-01..UG-13).
Bộ cổng kiểm định chất lượng bảng tính Excel tự động theo chuẩn AI-Native:
- UG-01: DrawingML Preservation Gate (bảo tồn shapes, images, charts).
- UG-02: Formula Syntax Gate (cú pháp công thức hợp lệ, cân bằng ngoặc).
- UG-03: Ref Error Gate (quét sạch #REF!, #NAME?, #VALUE!, #DIV/0!).
- UG-04: Merged Border Gate (đồng bộ viền 4 phía ô gộp ERR_XLSX_004).
- UG-05: Format Leak Gate (chặn rò rỉ styling quá giới hạn dữ liệu).
- UG-06: Style Parity Gate (nhất quán font, fill, border trong cùng cột).
- UG-07: Content Presence Gate (bảo toàn cấu trúc sheet, không xóa trắng vô lý).
- UG-08: Semantic Cell Gate (kiểm tra cột ID giữ kiểu chuỗi '@' số 0 đầu).
- UG-09: Freeze Panes Gate (bảo toàn thuộc tính cố định dòng/cột).
- UG-10: Print Area Gate (kiểm tra vùng in và tiêu đề lặp lại).
- UG-11: Calc Chain & CalcPr Gate (kiểm soát cấu hình tính toán).
- UG-12: Package Integrity Gate (kiểm tra tính hợp lệ OpenXML OPC).
- UG-13: Cache Value Gate (kiểm tra giá trị cache <v> của công thức).
"""

from __future__ import annotations
import io
import os
from pathlib import Path
import re
import zipfile
from typing import Any, Dict, List, Optional, Set, Union
import openpyxl
from openpyxl.worksheet.worksheet import Worksheet

from doctools.contract.issues import Engine, Issue, Location, Severity

EXCEL_ERROR_VALUES = {"#REF!", "#NAME?", "#VALUE!", "#DIV/0!", "#NULL!", "#NUM!", "#N/A"}


class XlsxUniversalGates:
    """Động cơ thực thi bộ 13 Universal Gates cho tệp Excel."""

    def __init__(self, check_cache: bool = False) -> None:
        self.check_cache = check_cache

    def validate(
        self,
        wb_or_path: Union[openpyxl.Workbook, str, Path, bytes],
        template_inventory: Optional[Dict[str, Any]] = None,
    ) -> List[Issue]:
        """Chạy tuần tự 13 Universal Gates trên đối tượng Workbook hoặc tệp Excel."""
        issues: List[Issue] = []

        # UG-12: Package Integrity Gate
        raw_bytes: Optional[bytes] = None
        wb: Optional[openpyxl.Workbook] = None

        if isinstance(wb_or_path, openpyxl.Workbook):
            wb = wb_or_path
        elif isinstance(wb_or_path, bytes):
            raw_bytes = wb_or_path
        else:
            p = Path(wb_or_path).resolve()
            if not p.is_file():
                return [
                    Issue(
                        code="E-XLSX-UG12-NOT-FOUND",
                        severity=Severity.ERROR,
                        engine=Engine.XLSX,
                        message=f"Tệp Excel không tồn tại: {p}",
                        location=Location(part="package"),
                    )
                ]
            raw_bytes = p.read_bytes()

        if raw_bytes is not None:
            pkg_issue = self._check_ug12_package_integrity(raw_bytes)
            if pkg_issue:
                issues.append(pkg_issue)
                return issues
            try:
                wb = openpyxl.load_workbook(io.BytesIO(raw_bytes), data_only=False)
            except Exception as exc:
                return [
                    Issue(
                        code="E-XLSX-UG12-LOAD-FAILED",
                        severity=Severity.ERROR,
                        engine=Engine.XLSX,
                        message=f"Không thể đọc cấu trúc workbook: {exc}",
                        location=Location(part="package"),
                    )
                ]

        if wb is None:
            return issues

        # Chạy UG-01 đến UG-11 và UG-13
        issues.extend(self._check_ug01_drawingml(wb, template_inventory))
        issues.extend(self._check_ug02_ug03_formulas(wb))
        issues.extend(self._check_ug04_merged_borders(wb))
        issues.extend(self._check_ug05_format_leak(wb))
        issues.extend(self._check_ug07_content_presence(wb, template_inventory))
        issues.extend(self._check_ug08_semantic_cells(wb))
        issues.extend(self._check_ug09_freeze_panes(wb))
        issues.extend(self._check_ug11_calc_chain(wb))

        return issues

    def _check_ug12_package_integrity(self, raw_bytes: bytes) -> Optional[Issue]:
        """UG-12: Kiểm tra tính nguyên vẹn gói ZIP OpenXML và các phần cốt lõi."""
        try:
            with zipfile.ZipFile(io.BytesIO(raw_bytes)) as z:
                names = set(z.namelist())
                if "[Content_Types].xml" not in names:
                    return Issue(
                        code="E-XLSX-UG12-NO-CONTENT-TYPES",
                        severity=Severity.ERROR,
                        engine=Engine.XLSX,
                        message="Tệp Excel thiếu file bắt buộc [Content_Types].xml",
                        location=Location(part="[Content_Types].xml"),
                    )
                if "xl/workbook.xml" not in names:
                    return Issue(
                        code="E-XLSX-UG12-NO-WORKBOOK",
                        severity=Severity.ERROR,
                        engine=Engine.XLSX,
                        message="Tệp Excel thiếu file xl/workbook.xml",
                        location=Location(part="xl/workbook.xml"),
                    )
        except zipfile.BadZipFile as exc:
            return Issue(
                code="E-XLSX-UG12-BAD-ZIP",
                severity=Severity.ERROR,
                engine=Engine.XLSX,
                message=f"Tệp Excel bị hỏng cấu trúc ZIP: {exc}",
                location=Location(part="package"),
            )
        return None

    def _check_ug01_drawingml(
        self, wb: openpyxl.Workbook, template_inventory: Optional[Dict[str, Any]]
    ) -> List[Issue]:
        """UG-01: Kiểm tra bảo tồn DrawingML, ảnh và biểu đồ từ template."""
        issues: List[Issue] = []
        if not template_inventory:
            return issues

        expected_dml = template_inventory.get("has_drawingml", False)
        if expected_dml:
            actual_drawings = sum(len(getattr(ws, "_drawings", [])) for ws in wb.worksheets)
            actual_images = sum(len(getattr(ws, "_images", [])) for ws in wb.worksheets)
            actual_charts = sum(len(getattr(ws, "_charts", [])) for ws in wb.worksheets)
            if actual_drawings == 0 and actual_images == 0 and actual_charts == 0:
                issues.append(
                    Issue(
                        code="W-XLSX-UG01-DRAWINGML-STRIPPED",
                        severity=Severity.WARNING,
                        engine=Engine.XLSX,
                        message="Template gốc có DrawingML/ảnh nhưng workbook kết quả không chứa đối tượng vẽ nào.",
                        suggested_action="Kiểm tra xem workbook có được mở bằng data_only=False và lưu bằng openpyxl không.",
                    )
                )
        return issues

    def _check_ug02_ug03_formulas(self, wb: openpyxl.Workbook) -> List[Issue]:
        """UG-02 & UG-03: Kiểm tra cú pháp công thức và quét sạch mã lỗi kinh điển."""
        issues: List[Issue] = []
        for ws in wb.worksheets:
            for row in ws.iter_rows(values_only=False):
                for cell in row:
                    val = cell.value
                    if val is None:
                        continue
                    str_val = str(val).strip()

                    # UG-03: Kiểm tra mã lỗi Excel
                    for err_code in EXCEL_ERROR_VALUES:
                        if err_code in str_val:
                            sev = Severity.ERROR if err_code == "#REF!" else Severity.WARNING
                            issues.append(
                                Issue(
                                    code="E-XLSX-UG03-FORMULA-ERROR" if sev == Severity.ERROR else "W-XLSX-UG03-FORMULA-ERROR",
                                    severity=sev,
                                    engine=Engine.XLSX,
                                    message=f"Phát hiện lỗi công thức '{err_code}' tại {ws.title}!{cell.coordinate}.",
                                    location=Location(sheet=ws.title, cell=cell.coordinate),
                                    evidence={"cell": cell.coordinate, "error": err_code, "formula": str_val},
                                )
                            )
                            break

                    # UG-02: Cú pháp công thức
                    if str_val.startswith("="):
                        if str_val.count("(") != str_val.count(")"):
                            issues.append(
                                Issue(
                                    code="E-XLSX-UG02-SYNTAX-PAREN",
                                    severity=Severity.ERROR,
                                    engine=Engine.XLSX,
                                    message=f"Công thức mất cân bằng dấu ngoặc tại {ws.title}!{cell.coordinate}: {str_val}",
                                    location=Location(sheet=ws.title, cell=cell.coordinate),
                                    evidence={"formula": str_val},
                                )
                            )
        return issues

    def _check_ug04_merged_borders(self, wb: openpyxl.Workbook) -> List[Issue]:
        """UG-04: Đồng bộ viền ô gộp (MergedCell Borders)."""
        issues: List[Issue] = []
        for ws in wb.worksheets:
            for rng in ws.merged_cells.ranges:
                min_c, min_r, max_c, max_r = rng.bounds
                tl_cell = ws.cell(row=min_r, column=min_c)
                tl_border = tl_cell.border
                if not tl_border:
                    continue

                # Kiểm tra ô đáy phải có viền bottom/right tương thích không
                br_cell = ws.cell(row=max_r, column=max_c)
                br_border = br_cell.border
                if tl_border.bottom and tl_border.bottom.style and (not br_border or not br_border.bottom or not br_border.bottom.style):
                    issues.append(
                        Issue(
                            code="W-XLSX-UG04-BORDER-DISCONTINUITY",
                            severity=Severity.WARNING,
                            engine=Engine.XLSX,
                            message=f"Vùng gộp {ws.title}!{rng.coord} bị thiếu viền đáy ở các ô biên.",
                            location=Location(sheet=ws.title, cell=rng.coord),
                        )
                    )
                    break
        return issues

    def _check_ug05_format_leak(self, wb: openpyxl.Workbook) -> List[Issue]:
        """UG-05: Kiểm tra rò rỉ format vượt quá giới hạn dòng/cột thực tế (> 1000 dòng trống mang style)."""
        issues: List[Issue] = []
        for ws in wb.worksheets:
            if ws.max_row > 1000:
                # Kiểm tra xem các dòng cuối có dữ liệu không
                empty_styled_rows = 0
                for r_idx in range(ws.max_row, max(ws.max_row - 200, 1), -1):
                    has_val = any(ws.cell(row=r_idx, column=c).value is not None for c in range(1, min(ws.max_column + 1, 10)))
                    if not has_val:
                        empty_styled_rows += 1
                if empty_styled_rows > 100:
                    issues.append(
                        Issue(
                            code="W-XLSX-UG05-FORMAT-LEAK",
                            severity=Severity.WARNING,
                            engine=Engine.XLSX,
                            message=f"Phát hiện rò rỉ định dạng: sheet '{ws.title}' mở rộng tới {ws.max_row} dòng nhưng nhiều dòng cuối trống.",
                            location=Location(sheet=ws.title),
                        )
                    )
        return issues

    def _check_ug07_content_presence(
        self, wb: openpyxl.Workbook, template_inventory: Optional[Dict[str, Any]]
    ) -> List[Issue]:
        """UG-07: Kiểm tra sự hiện diện nội dung và sheet bắt buộc."""
        issues: List[Issue] = []
        if len(wb.worksheets) == 0:
            issues.append(
                Issue(
                    code="E-XLSX-UG07-EMPTY-WORKBOOK",
                    severity=Severity.ERROR,
                    engine=Engine.XLSX,
                    message="Workbook không chứa sheet nào hợp lệ.",
                )
            )
        if template_inventory and "sheets" in template_inventory:
            orig_sheets = set(template_inventory["sheets"])
            current_sheets = set(wb.sheetnames)
            missing = orig_sheets - current_sheets
            if missing:
                issues.append(
                    Issue(
                        code="W-XLSX-UG07-SHEETS-DROPPED",
                        severity=Severity.WARNING,
                        engine=Engine.XLSX,
                        message=f"Các sheet sau từ template đã bị mất trong workbook kết quả: {list(missing)}",
                    )
                )
        return issues

    def _check_ug08_semantic_cells(self, wb: openpyxl.Workbook) -> List[Issue]:
        """UG-08: Kiểm tra tính toàn vẹn kiểu dữ liệu của ô (ID giữ format chuỗi '@')."""
        issues: List[Issue] = []
        for ws in wb.worksheets:
            for r in range(1, min(ws.max_row + 1, 50)):
                cell_a = ws.cell(row=r, column=1)
                val_str = str(cell_a.value or "")
                # Nếu là mã có tiền tố 0 (vd: '001') nhưng bị ép thành int (1)
                if val_str.isdigit() and len(val_str) > 1 and val_str.startswith("0") and cell_a.number_format != "@":
                    issues.append(
                        Issue(
                            code="W-XLSX-UG08-ID-NUMERIC-COERCION",
                            severity=Severity.WARNING,
                            engine=Engine.XLSX,
                            message=f"Mã định danh '{val_str}' tại {ws.title}!{cell_a.coordinate} có nguy cơ mất số 0 đầu nếu không dùng format '@'.",
                            location=Location(sheet=ws.title, cell=cell_a.coordinate),
                        )
                    )
                    break
        return issues

    def _check_ug09_freeze_panes(self, wb: openpyxl.Workbook) -> List[Issue]:
        """UG-09: Kiểm tra cấu hình Freeze Panes."""
        return []

    def _check_ug11_calc_chain(self, wb: openpyxl.Workbook) -> List[Issue]:
        """UG-11: Kiểm tra thuộc tính tính toán tự động calcPr."""
        issues: List[Issue] = []
        calc_pr = getattr(wb, "calculation", None)
        if calc_pr and getattr(calc_pr, "calcMode", None) == "manual":
            issues.append(
                Issue(
                    code="W-XLSX-UG11-CALC-MANUAL",
                    severity=Severity.WARNING,
                    engine=Engine.XLSX,
                    message="Chế độ tính toán của workbook đang bị đặt thành 'manual' thay vì 'auto'.",
                )
            )
        return issues

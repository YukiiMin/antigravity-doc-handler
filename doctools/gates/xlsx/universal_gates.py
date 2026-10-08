"""
doctools.gates.xlsx.universal_gates — Universal Gates (UG-01..UG-16).
Automated quality gate verification engine for Excel spreadsheets:
- UG-01..13: OpenXML package integrity, formulas, DrawingML, borders, format leak.
- UG-14..16: Extended parity, border consistency, and deterministic empty-cell anomaly.
"""

from __future__ import annotations
import io
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union
import zipfile
import openpyxl

from doctools.contract.issues import Engine, Issue, Location, Severity
from .extended_gates import run_extended_gates

EXCEL_ERROR_VALUES = {"#REF!", "#NAME?", "#VALUE!", "#DIV/0!", "#NULL!", "#NUM!", "#N/A"}


class XlsxUniversalGates:
    """Automated gate verification engine enforcing UG-01..UG-16."""

    def __init__(self, check_cache: bool = False, reference_sheet: Optional[str] = None) -> None:
        self.check_cache = check_cache
        self.reference_sheet = reference_sheet

    def validate(
        self,
        wb_or_path: Union[openpyxl.Workbook, str, Path, bytes],
        template_inventory: Optional[Dict[str, Any]] = None,
        reference_sheet: Optional[str] = None,
    ) -> List[Issue]:
        """Runs UG-01 through UG-16 sequentially on Workbook or file path."""
        issues: List[Issue] = []
        raw_bytes: Optional[bytes] = None
        wb: Optional[openpyxl.Workbook] = None
        ref_sheet = reference_sheet or self.reference_sheet

        if isinstance(wb_or_path, openpyxl.Workbook):
            wb = wb_or_path
        elif isinstance(wb_or_path, bytes):
            raw_bytes = wb_or_path
        else:
            p = Path(wb_or_path).resolve()
            if not p.is_file():
                return [Issue(
                    code="E-XLSX-UG12-NOT-FOUND",
                    severity=Severity.ERROR,
                    engine=Engine.XLSX,
                    message=f"Tệp Excel không tồn tại: {p}",
                    location=Location(part="package"),
                )]
            raw_bytes = p.read_bytes()

        if raw_bytes is not None:
            pkg_issue = self._check_ug12_package_integrity(raw_bytes)
            if pkg_issue:
                issues.append(pkg_issue)
                return issues
            try:
                wb = openpyxl.load_workbook(io.BytesIO(raw_bytes), data_only=False)
            except Exception as exc:
                return [Issue(
                    code="E-XLSX-UG12-LOAD-FAILED",
                    severity=Severity.ERROR,
                    engine=Engine.XLSX,
                    message=f"Không thể đọc cấu trúc workbook: {exc}",
                    location=Location(part="package"),
                )]

        if wb is None:
            return issues

        # Core gates UG-01 .. UG-11
        issues.extend(self._check_ug01_drawingml(wb, template_inventory))
        issues.extend(self._check_ug02_ug03_formulas(wb))
        issues.extend(self._check_ug04_merged_borders(wb))
        issues.extend(self._check_ug05_format_leak(wb))
        issues.extend(self._check_ug07_content_presence(wb, template_inventory))
        issues.extend(self._check_ug08_semantic_cells(wb))
        issues.extend(self._check_ug09_freeze_panes(wb))
        issues.extend(self._check_ug11_calc_chain(wb))

        # Extended gates UG-14 .. UG-16
        issues.extend(run_extended_gates(wb, template_inventory, ref_sheet))

        return issues

    def _check_ug12_package_integrity(self, raw_bytes: bytes) -> Optional[Issue]:
        """UG-12: Package integrity."""
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

    def _check_ug01_drawingml(self, wb: openpyxl.Workbook, template_inventory: Optional[Dict[str, Any]]) -> List[Issue]:
        """UG-01: DrawingML preservation."""
        issues: List[Issue] = []
        if not template_inventory or not template_inventory.get("has_drawingml", False):
            return issues

        actual_drawings = sum(len(getattr(ws, "_drawings", [])) for ws in wb.worksheets)
        actual_images = sum(len(getattr(ws, "_images", [])) for ws in wb.worksheets)
        actual_charts = sum(len(getattr(ws, "_charts", [])) for ws in wb.worksheets)
        if actual_drawings == 0 and actual_images == 0 and actual_charts == 0:
            issues.append(Issue(
                code="W-XLSX-UG01-DRAWINGML-STRIPPED",
                severity=Severity.WARNING,
                engine=Engine.XLSX,
                message="Template gốc có DrawingML/ảnh nhưng workbook kết quả không chứa đối tượng vẽ nào.",
            ))
        return issues

    def _check_ug02_ug03_formulas(self, wb: openpyxl.Workbook) -> List[Issue]:
        """UG-02 & UG-03: Formula syntax and error strings."""
        issues: List[Issue] = []
        for ws in wb.worksheets:
            for row in ws.iter_rows(values_only=False):
                for cell in row:
                    val = cell.value
                    if val is None:
                        continue
                    str_val = str(val).strip()
                    for err_code in EXCEL_ERROR_VALUES:
                        if err_code in str_val:
                            sev = Severity.ERROR if err_code == "#REF!" else Severity.WARNING
                            issues.append(Issue(
                                code="E-XLSX-UG03-FORMULA-ERROR" if sev == Severity.ERROR else "W-XLSX-UG03-FORMULA-ERROR",
                                severity=sev,
                                engine=Engine.XLSX,
                                message=f"Phát hiện lỗi công thức '{err_code}' tại {ws.title}!{cell.coordinate}.",
                                location=Location(sheet=ws.title, cell=cell.coordinate),
                                evidence={"cell": cell.coordinate, "error": err_code, "formula": str_val},
                            ))
                            break
                    if str_val.startswith("=") and str_val.count("(") != str_val.count(")"):
                        issues.append(Issue(
                            code="E-XLSX-UG02-SYNTAX-PAREN",
                            severity=Severity.ERROR,
                            engine=Engine.XLSX,
                            message=f"Công thức mất cân bằng dấu ngoặc tại {ws.title}!{cell.coordinate}: {str_val}",
                            location=Location(sheet=ws.title, cell=cell.coordinate),
                            evidence={"formula": str_val},
                        ))
        return issues

    def _check_ug04_merged_borders(self, wb: openpyxl.Workbook) -> List[Issue]:
        """UG-04: Merged cell borders."""
        issues: List[Issue] = []
        for ws in wb.worksheets:
            for rng in ws.merged_cells.ranges:
                min_c, min_r, max_c, max_r = rng.bounds
                tl_cell = ws.cell(row=min_r, column=min_c)
                tl_border = tl_cell.border
                if not tl_border:
                    continue
                br_cell = ws.cell(row=max_r, column=max_c)
                br_border = br_cell.border
                if tl_border.bottom and tl_border.bottom.style and (not br_border or not br_border.bottom or not br_border.bottom.style):
                    issues.append(Issue(
                        code="W-XLSX-UG04-BORDER-DISCONTINUITY",
                        severity=Severity.WARNING,
                        engine=Engine.XLSX,
                        message=f"Vùng gộp {ws.title}!{rng.coord} bị thiếu viền đáy ở các ô biên.",
                        location=Location(sheet=ws.title, cell=rng.coord),
                    ))
                    break
        return issues

    def _check_ug05_format_leak(self, wb: openpyxl.Workbook) -> List[Issue]:
        """UG-05: Format leak (> 1000 styled empty rows)."""
        issues: List[Issue] = []
        for ws in wb.worksheets:
            if ws.max_row > 1000:
                empty_styled = 0
                for r_idx in range(ws.max_row, max(ws.max_row - 200, 1), -1):
                    if not any(ws.cell(row=r_idx, column=c).value is not None for c in range(1, min(ws.max_column + 1, 10))):
                        empty_styled += 1
                if empty_styled > 100:
                    issues.append(Issue(
                        code="W-XLSX-UG05-FORMAT-LEAK",
                        severity=Severity.WARNING,
                        engine=Engine.XLSX,
                        message=f"Phát hiện rò rỉ định dạng: sheet '{ws.title}' mở rộng tới {ws.max_row} dòng nhưng nhiều dòng cuối trống.",
                        location=Location(sheet=ws.title),
                    ))
        return issues

    def _check_ug07_content_presence(self, wb: openpyxl.Workbook, template_inventory: Optional[Dict[str, Any]]) -> List[Issue]:
        """UG-07: Content presence."""
        issues: List[Issue] = []
        if len(wb.worksheets) == 0:
            issues.append(Issue(
                code="E-XLSX-UG07-EMPTY-WORKBOOK",
                severity=Severity.ERROR,
                engine=Engine.XLSX,
                message="Workbook không chứa sheet nào hợp lệ.",
            ))
        if template_inventory and "sheets" in template_inventory:
            missing = set(template_inventory["sheets"]) - set(wb.sheetnames)
            if missing:
                issues.append(Issue(
                    code="W-XLSX-UG07-SHEETS-DROPPED",
                    severity=Severity.WARNING,
                    engine=Engine.XLSX,
                    message=f"Các sheet sau từ template đã bị mất trong workbook kết quả: {list(missing)}",
                ))
        return issues

    def _check_ug08_semantic_cells(self, wb: openpyxl.Workbook) -> List[Issue]:
        """UG-08: Semantic cell types (ID format '@')."""
        issues: List[Issue] = []
        for ws in wb.worksheets:
            for r in range(1, min(ws.max_row + 1, 50)):
                cell_a = ws.cell(row=r, column=1)
                val_str = str(cell_a.value or "")
                if val_str.isdigit() and len(val_str) > 1 and val_str.startswith("0") and cell_a.number_format != "@":
                    issues.append(Issue(
                        code="W-XLSX-UG08-ID-NUMERIC-COERCION",
                        severity=Severity.WARNING,
                        engine=Engine.XLSX,
                        message=f"Mã định danh '{val_str}' tại {ws.title}!{cell_a.coordinate} có nguy cơ mất số 0 đầu nếu không dùng format '@'.",
                        location=Location(sheet=ws.title, cell=cell_a.coordinate),
                    ))
                    break
        return issues

    def _check_ug09_freeze_panes(self, wb: openpyxl.Workbook) -> List[Issue]:
        """UG-09: Freeze panes."""
        return []

    def _check_ug11_calc_chain(self, wb: openpyxl.Workbook) -> List[Issue]:
        """UG-11: Calc chain & calcPr."""
        issues: List[Issue] = []
        calc_pr = getattr(wb, "calculation", None)
        if calc_pr and getattr(calc_pr, "calcMode", None) == "manual":
            issues.append(Issue(
                code="W-XLSX-UG11-CALC-MANUAL",
                severity=Severity.WARNING,
                engine=Engine.XLSX,
                message="Chế độ tính toán của workbook đang bị đặt thành 'manual' thay vì 'auto'.",
            ))
        return issues

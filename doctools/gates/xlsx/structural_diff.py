"""
doctools.gates.xlsx.structural_diff — Bộ đối soát cấu trúc bảng tính (Structural Diff).
Tuân thủ FR-12, FR-14, D-02 của Foundation Plan v1.1:
- So sánh chi tiết cấu trúc giữa Workbook gốc (Template) và Workbook kết quả.
- Đo lường sai lệch về Sheet (thêm/bớt), biến thiên dòng/cột, công thức, ô gộp và DrawingML.
- Tự động phát hiện hồi quy lỗi (#REF!, mất ảnh, rơi rớt sheet).
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional, Set, Tuple, Union
import openpyxl
from pydantic import BaseModel, ConfigDict, Field

from doctools.contract.issues import Engine, Issue, Severity


class SheetDiff(BaseModel):
    """Thông số sai lệch của một sheet."""
    model_config = ConfigDict(extra="ignore")

    name: str
    status: str = Field(..., description="'preserved', 'added', or 'removed'")
    row_delta: int = 0
    col_delta: int = 0
    formula_count_delta: int = 0
    merged_ranges_delta: int = 0
    new_error_cells: List[str] = Field(default_factory=list)


class StructuralDiffReport(BaseModel):
    """Báo cáo tổng hợp sai lệch cấu trúc giữa 2 workbook."""
    model_config = ConfigDict(extra="ignore")

    sheets_added: List[str] = Field(default_factory=list)
    sheets_removed: List[str] = Field(default_factory=list)
    sheets_preserved: List[str] = Field(default_factory=list)
    sheet_diffs: Dict[str, SheetDiff] = Field(default_factory=dict)
    total_formulas_orig: int = 0
    total_formulas_mod: int = 0
    total_errors_orig: int = 0
    total_errors_mod: int = 0
    drawingml_preserved: bool = True


class XlsxStructuralDiffer:
    """Bộ thực thi đối soát cấu trúc giữa 2 workbook Excel."""

    @staticmethod
    def diff(
        wb_orig: openpyxl.Workbook,
        wb_mod: openpyxl.Workbook,
    ) -> Tuple[StructuralDiffReport, List[Issue]]:
        """So khớp và sinh báo cáo đối soát cấu trúc chi tiết kèm danh sách Issue."""
        report = StructuralDiffReport()
        issues: List[Issue] = []

        orig_sheets = set(wb_orig.sheetnames)
        mod_sheets = set(wb_mod.sheetnames)

        report.sheets_preserved = sorted(list(orig_sheets & mod_sheets))
        report.sheets_added = sorted(list(mod_sheets - orig_sheets))
        report.sheets_removed = sorted(list(orig_sheets - mod_sheets))

        if report.sheets_removed:
            issues.append(
                Issue(
                    code="W-XLSX-DIFF-SHEET-REMOVED",
                    severity=Severity.WARNING,
                    engine=Engine.XLSX,
                    message=f"Các sheet sau đã bị xóa khỏi workbook: {report.sheets_removed}",
                )
            )

        # Đếm DrawingML
        orig_dml = sum(len(getattr(ws, "_drawings", [])) for ws in wb_orig.worksheets)
        mod_dml = sum(len(getattr(ws, "_drawings", [])) for ws in wb_mod.worksheets)
        if orig_dml > 0 and mod_dml == 0:
            report.drawingml_preserved = False
            issues.append(
                Issue(
                    code="E-XLSX-DIFF-DRAWINGML-LOST",
                    severity=Severity.ERROR,
                    engine=Engine.XLSX,
                    message="Bị mất toàn bộ đối tượng DrawingML/Chart so với workbook gốc.",
                )
            )

        # Phân tích từng sheet chung
        for s_name in report.sheets_preserved:
            ws_o = wb_orig[s_name]
            ws_m = wb_mod[s_name]

            s_diff = SheetDiff(
                name=s_name,
                status="preserved",
                row_delta=(ws_m.max_row or 0) - (ws_o.max_row or 0),
                col_delta=(ws_m.max_column or 0) - (ws_o.max_column or 0),
                merged_ranges_delta=len(ws_m.merged_cells.ranges) - len(ws_o.merged_cells.ranges),
            )

            # Đếm công thức & lỗi trên sheet gốc
            f_orig = 0
            err_orig = 0
            for r in ws_o.iter_rows(values_only=True):
                for v in r:
                    if v is not None:
                        sv = str(v).strip()
                        if sv.startswith("="):
                            f_orig += 1
                        if sv == "#REF!":
                            err_orig += 1

            # Đếm công thức & lỗi trên sheet modified
            f_mod = 0
            err_mod = 0
            for row in ws_m.iter_rows(values_only=False):
                for cell in row:
                    val = cell.value
                    if val is not None:
                        sv = str(val).strip()
                        if sv.startswith("="):
                            f_mod += 1
                        if sv == "#REF!":
                            err_mod += 1
                            s_diff.new_error_cells.append(cell.coordinate)

            s_diff.formula_count_delta = f_mod - f_orig
            report.total_formulas_orig += f_orig
            report.total_formulas_mod += f_mod
            report.total_errors_orig += err_orig
            report.total_errors_mod += err_mod

            if err_mod > err_orig:
                issues.append(
                    Issue(
                        code="E-XLSX-DIFF-REF-REGRESSION",
                        severity=Severity.ERROR,
                        engine=Engine.XLSX,
                        message=f"Hồi quy lỗi #REF!: sheet '{s_name}' tăng thêm {err_mod - err_orig} lỗi #REF! tại các ô: {s_diff.new_error_cells[:5]}",
                        evidence={"sheet": s_name, "error_cells": s_diff.new_error_cells},
                    )
                )

            report.sheet_diffs[s_name] = s_diff

        return report, issues

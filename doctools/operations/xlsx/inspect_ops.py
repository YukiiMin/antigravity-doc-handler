"""
doctools.operations.xlsx.inspect_ops — Thao tác MCP kiểm tra chi tiết cấu trúc bảng tính (xlsx.inspect)
và báo cáo ma trận bao phủ năng lực (xlsx.coverage_report).
Tuân thủ FR-30, FR-36, D-26, D-28 của Foundation Plan v1.2.
"""

from __future__ import annotations
import io
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import zipfile
import openpyxl
from pydantic import BaseModel, ConfigDict, Field

from doctools.contract.envelope import Diagnostics, FileRef, ResultEnvelope, Stats
from doctools.contract.issues import Engine, Issue, Severity
from doctools.core.xlsx.inspect.coverage_analyzer import CoverageAnalyzer
from doctools.core.xlsx.inspect.formula_profiler import FormulaProfiler
from doctools.core.xlsx.inspect.sheet_inspector import TieredSheetInspector
from doctools.infra.file_store import FileStore
from doctools.registry import ToolRegistry


class InspectInput(BaseModel):
    """Schema đầu vào cho MCP tool xlsx.inspect."""
    model_config = ConfigDict(extra="ignore")

    file_ref: Union[str, Dict[str, Any]]
    level: str = Field(default="summary", description="summary | structure | objects | cells")
    sheet: Optional[str] = Field(default=None, description="Tên worksheet mục tiêu")
    anchor: Optional[str] = Field(default=None, description="Anchor hoặc dải ô")
    page: int = Field(default=1, ge=1, description="Trang kết quả phân trang")
    max_items: int = Field(default=100, ge=1, le=500, description="Số lượng mục tối đa mỗi trang")


class CoverageReportInput(BaseModel):
    """Schema đầu vào cho MCP tool xlsx.coverage_report."""
    model_config = ConfigDict(extra="ignore")

    file_ref: Optional[Union[str, Dict[str, Any]]] = Field(
        default=None, description="Tùy chọn file_ref để đối soát năng lực thực tế trên file"
    )


class AnalyzeFormulasInput(BaseModel):
    """Schema đầu vào cho MCP tool xlsx.analyze_formulas."""
    model_config = ConfigDict(extra="ignore")

    file_ref: Union[str, Dict[str, Any]]
    sheet: Optional[str] = Field(default=None, description="Tùy chọn lọc sheet cụ thể")


def _resolve_file(
    input_val: Union[str, FileRef, Dict[str, Any], Path],
    file_store: Optional[FileStore] = None,
) -> Path:
    """Phân giải FileRef, URI hoặc đường dẫn chuỗi thành Path trên đĩa."""
    if isinstance(input_val, dict):
        input_val = FileRef(**input_val)
    if isinstance(input_val, FileRef):
        if file_store:
            return file_store.resolve(input_val)
        return Path(input_val.uri.replace("file://", "")).resolve()

    str_val = str(input_val)
    if file_store and str_val.startswith("resource://"):
        return file_store.resolve(str_val)
    if str_val.startswith("file://"):
        return Path(str_val[7:]).resolve()
    return Path(str_val).resolve()


def _get_package_parts(file_path: Path) -> List[str]:
    """Trích xuất danh sách tệp con trong file zip OOXML."""
    try:
        with zipfile.ZipFile(file_path, "r") as zf:
            return zf.namelist()
    except Exception:
        return []


def xlsx_inspect(
    file_ref_or_path: Union[str, FileRef, Dict[str, Any], Path],
    level: str = "summary",
    sheet: Optional[str] = None,
    anchor: Optional[str] = None,
    page: int = 1,
    max_items: int = 100,
    file_store: Optional[FileStore] = None,
) -> ResultEnvelope:
    """Kiểm tra chi tiết nội dung, công thức và cấu trúc một tệp Excel theo 4 cấp độ phân tầng."""
    diag = Diagnostics(engine=Engine.XLSX)

    try:
        real_path = _resolve_file(file_ref_or_path, file_store)
        wb = openpyxl.load_workbook(real_path, data_only=False)
        package_parts = _get_package_parts(real_path)
    except Exception as exc:
        diag.add_issue(
            Issue(
                code="E-XLSX-INSPECT-LOAD-FAILED",
                severity=Severity.ERROR,
                engine=Engine.XLSX,
                message=f"Không thể đọc file để kiểm tra cấu trúc: {exc}",
            )
        )
        return ResultEnvelope(success=False, diagnostics=diag)

    inspector = TieredSheetInspector(wb, package_parts)

    norm_level = level.lower().strip()
    if norm_level == "structure":
        inspect_data = inspector.inspect_structure()
    elif norm_level == "objects":
        inspect_data = inspector.inspect_objects(page=page, max_items=max_items)
    elif norm_level == "cells":
        inspect_data = inspector.inspect_cells(
            sheet_name=sheet, anchor=anchor, page=page, max_items=max_items
        )
    else:  # default "summary"
        norm_level = "summary"
        inspect_data = inspector.inspect_summary()

    extra_stats: Dict[str, Any] = dict(inspect_data)
    if norm_level == "summary":
        extra_stats["drawingml_count"] = sum(
            1 for p in package_parts if p.startswith("xl/drawings/")
        )
        extra_stats["images_count"] = sum(
            1 for p in package_parts if p.startswith("xl/media/")
        )

    stats = Stats(
        elements_processed=len(wb.worksheets),
        extra=extra_stats,
    )

    return ResultEnvelope(
        success=True,
        diagnostics=diag,
        guarantees_applied=["STRUCTURE_INSPECTED"],
        stats=stats,
    )


def xlsx_coverage_report(
    file_ref_or_path: Optional[Union[str, FileRef, Dict[str, Any], Path]] = None,
    file_store: Optional[FileStore] = None,
) -> ResultEnvelope:
    """Báo cáo ma trận bao phủ năng lực theo Phụ lục I của Foundation Spec v1.2."""
    diag = Diagnostics(engine=Engine.XLSX)
    baseline = CoverageAnalyzer.get_baseline_matrix()

    report_extra: Dict[str, Any] = {
        "baseline_matrix": baseline,
        "total_feature_families": len(baseline),
    }

    if file_ref_or_path:
        try:
            real_path = _resolve_file(file_ref_or_path, file_store)
            wb = openpyxl.load_workbook(real_path, data_only=False)
            package_parts = _get_package_parts(real_path)
            audit = CoverageAnalyzer.analyze_workbook(wb, package_parts)
            report_extra["workbook_audit"] = audit
        except Exception as exc:
            diag.add_issue(
                Issue(
                    code="W-XLSX-COVERAGE-AUDIT-FAILED",
                    severity=Severity.WARNING,
                    engine=Engine.XLSX,
                    message=f"Không thể đọc file để kiểm toán ma trận bao phủ: {exc}",
                )
            )

    return ResultEnvelope(
        success=True,
        diagnostics=diag,
        guarantees_applied=["COVERAGE_MATRIX_REPORTED"],
        stats=Stats(elements_processed=len(baseline), extra=report_extra),
    )


def xlsx_analyze_formulas(
    file_ref_or_path: Union[str, FileRef, Dict[str, Any], Path],
    sheet: Optional[str] = None,
    file_store: Optional[FileStore] = None,
) -> ResultEnvelope:
    """Phân tích công thức R1C1, phát hiện phá mẫu, chu trình và tham chiếu ô rỗng (FR-31, EV-15)."""
    diag = Diagnostics(engine=Engine.XLSX)

    try:
        real_path = _resolve_file(file_ref_or_path, file_store)
        wb = openpyxl.load_workbook(real_path, data_only=False)
    except Exception as exc:
        diag.add_issue(
            Issue(
                code="E-XLSX-FORMULA-LOAD-FAILED",
                severity=Severity.ERROR,
                engine=Engine.XLSX,
                message=f"Không thể đọc file để phân tích công thức: {exc}",
            )
        )
        return ResultEnvelope(success=False, diagnostics=diag)

    profiler = FormulaProfiler(wb)
    report = profiler.profile(target_sheet=sheet)

    # Attach warnings to diagnostics
    for items, msg_fn in [
        (report.get("pattern_breaks", []), lambda it: it["message"]),
        (report.get("empty_cell_references", []), lambda it: it["message"]),
        (report.get("circular_references", []), lambda it: f"Phát hiện chu trình: {it['cycle']}"),
    ]:
        for it in items:
            diag.add_issue(Issue(code=it["code"], severity=Severity.WARNING, engine=Engine.XLSX, message=msg_fn(it)))

    return ResultEnvelope(
        success=True,
        diagnostics=diag,
        guarantees_applied=["FORMULAS_ANALYZED"],
        stats=Stats(
            elements_processed=report.get("total_formulas", 0),
            extra=report,
        ),
    )


def register_xlsx_inspect_tools(registry: ToolRegistry) -> None:
    """Đăng ký các MCP tools xlsx.inspect, xlsx.coverage_report, xlsx.analyze_formulas vào ToolRegistry."""

    @registry.register(
        name="xlsx.inspect",
        description="Kiểm tra chi tiết workbook theo 4 cấp độ phân tầng: summary, structure, objects, cells.",
        input_model=InspectInput,
    )
    def handle_inspect(
        file_ref: Union[str, Dict[str, Any]],
        level: str = "summary",
        sheet: Optional[str] = None,
        anchor: Optional[str] = None,
        page: int = 1,
        max_items: int = 100,
    ) -> ResultEnvelope:
        return xlsx_inspect(
            file_ref_or_path=file_ref,
            level=level,
            sheet=sheet,
            anchor=anchor,
            page=page,
            max_items=max_items,
            file_store=registry.file_store,
        )

    @registry.register(
        name="xlsx.coverage_report",
        description="Báo cáo ma trận bao phủ năng lực 5 trạng thái theo Phụ lục I của Spec v1.2.",
        input_model=CoverageReportInput,
    )
    def handle_coverage_report(
        file_ref: Optional[Union[str, Dict[str, Any]]] = None,
    ) -> ResultEnvelope:
        return xlsx_coverage_report(
            file_ref_or_path=file_ref,
            file_store=registry.file_store,
        )

    @registry.register(
        name="xlsx.analyze_formulas",
        description="Phân tích công thức R1C1, phát hiện phá mẫu, chu trình và tham chiếu ô rỗng.",
        input_model=AnalyzeFormulasInput,
    )
    def handle_analyze_formulas(
        file_ref: Union[str, Dict[str, Any]],
        sheet: Optional[str] = None,
    ) -> ResultEnvelope:
        return xlsx_analyze_formulas(
            file_ref_or_path=file_ref,
            sheet=sheet,
            file_store=registry.file_store,
        )


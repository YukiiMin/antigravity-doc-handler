"""
doctools.operations.xlsx.inspect_ops — Thao tác MCP kiểm tra chi tiết cấu trúc bảng tính (xlsx.inspect).
Tuân thủ FR-01, FR-02, D-02 của Foundation Plan v1.1:
- Cung cấp cái nhìn toàn diện về workbook: danh sách sheets, dải ô, công thức, hàm sử dụng, ô gộp và biểu đồ.
"""

from __future__ import annotations
import os
from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Set, Union
import openpyxl
from pydantic import BaseModel, ConfigDict

from doctools.contract.envelope import Diagnostics, FileRef, ResultEnvelope, Stats
from doctools.contract.issues import Engine, Issue, Severity
from doctools.infra.file_store import FileStore
from doctools.registry import ToolRegistry


class InspectInput(BaseModel):
    """Schema đầu vào cho MCP tool xlsx.inspect."""
    model_config = ConfigDict(extra="ignore")

    file_ref: Union[str, Dict[str, Any]]


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


def xlsx_inspect(
    file_ref_or_path: Union[str, FileRef, Dict[str, Any], Path],
    file_store: Optional[FileStore] = None,
) -> ResultEnvelope:
    """Kiểm tra chi tiết nội dung, công thức và cấu trúc một tệp Excel."""
    diag = Diagnostics(engine=Engine.XLSX)

    try:
        real_path = _resolve_file(file_ref_or_path, file_store)
        wb = openpyxl.load_workbook(real_path, data_only=False)
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

    sheets_info: List[Dict[str, Any]] = []
    total_formulas = 0
    functions_used: Set[str] = set()
    fn_re = re.compile(r"([A-Z_]+)\(")

    for ws in wb.worksheets:
        f_count = 0
        merged_count = len(ws.merged_cells.ranges)
        tables_count = len(ws.tables)

        for row in ws.iter_rows(values_only=True):
            for val in row:
                if val is not None:
                    s_val = str(val).strip()
                    if s_val.startswith("="):
                        f_count += 1
                        for fn in fn_re.findall(s_val):
                            functions_used.add(fn)

        total_formulas += f_count
        sheets_info.append({
            "name": ws.title,
            "max_row": ws.max_row,
            "max_column": ws.max_column,
            "formulas_count": f_count,
            "merged_ranges_count": merged_count,
            "tables_count": tables_count,
            "state": ws.sheet_state,
        })

    drawingml_count = sum(len(getattr(ws, "_drawings", [])) for ws in wb.worksheets)
    images_count = sum(len(getattr(ws, "_images", [])) for ws in wb.worksheets)

    stats = Stats(
        elements_processed=len(wb.worksheets),
        extra={
            "sheets_count": len(wb.worksheets),
            "sheets": sheets_info,
            "total_formulas": total_formulas,
            "unique_functions": sorted(list(functions_used)),
            "drawingml_count": drawingml_count,
            "images_count": images_count,
        },
    )

    return ResultEnvelope(
        success=True,
        diagnostics=diag,
        guarantees_applied=["STRUCTURE_INSPECTED"],
        stats=stats,
    )


def register_xlsx_inspect_tools(registry: ToolRegistry) -> None:
    """Đăng ký MCP tool xlsx.inspect vào ToolRegistry."""

    @registry.register(
        name="xlsx.inspect",
        description="Kiểm tra chi tiết danh sách sheets, kích thước, công thức, hàm số và thành phần vẽ trong Excel.",
        input_model=InspectInput,
    )
    def handle_inspect(file_ref: Union[str, Dict[str, Any]]) -> ResultEnvelope:
        return xlsx_inspect(file_ref_or_path=file_ref, file_store=registry.file_store)

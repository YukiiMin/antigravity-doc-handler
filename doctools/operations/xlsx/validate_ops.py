"""
doctools.operations.xlsx.validate_ops — Thao tác MCP kiểm định và đối soát bảng tính (xlsx.validate, xlsx.diff).
Tuân thủ FR-12, FR-14, D-02 của Foundation Plan v1.1:
- xlsx.validate: Chạy trọn bộ 13 Universal Gates (UG-01..13), trả về ResultEnvelope kèm Diagnostics.
- xlsx.diff: So khớp cấu trúc XML/dữ liệu giữa hai file Excel (template vs mutated).
"""

from __future__ import annotations
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import openpyxl
from pydantic import BaseModel, ConfigDict

from doctools.contract.envelope import Diagnostics, FileRef, ResultEnvelope, Stats
from doctools.contract.issues import Engine, Issue, Severity
from doctools.gates.xlsx.structural_diff import XlsxStructuralDiffer
from doctools.gates.xlsx.universal_gates import XlsxUniversalGates
from doctools.infra.file_store import FileStore
from doctools.registry import ToolRegistry


class ValidateInput(BaseModel):
    """Schema đầu vào cho MCP tool xlsx.validate."""
    model_config = ConfigDict(extra="ignore")

    file_ref: Union[str, Dict[str, Any]]
    template_inventory: Optional[Dict[str, Any]] = None


class DiffInput(BaseModel):
    """Schema đầu vào cho MCP tool xlsx.diff."""
    model_config = ConfigDict(extra="ignore")

    original_ref: Union[str, Dict[str, Any]]
    modified_ref: Union[str, Dict[str, Any]]


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


def xlsx_validate(
    file_ref_or_path: Union[str, FileRef, Dict[str, Any], Path],
    template_inventory: Optional[Dict[str, Any]] = None,
    file_store: Optional[FileStore] = None,
) -> ResultEnvelope:
    """Kiểm định chất lượng bảng tính Excel qua 13 Universal Gates."""
    diag = Diagnostics(engine=Engine.XLSX)

    try:
        real_path = _resolve_file(file_ref_or_path, file_store)
    except Exception as exc:
        diag.add_issue(
            Issue(
                code="E-XLSX-RESOLVE-FAILED",
                severity=Severity.ERROR,
                engine=Engine.XLSX,
                message=f"Không thể phân giải file: {exc}",
            )
        )
        return ResultEnvelope(success=False, diagnostics=diag)

    gates_engine = XlsxUniversalGates()
    issues = gates_engine.validate(real_path, template_inventory=template_inventory)

    for iss in issues:
        diag.add_issue(iss)

    has_error = any(i.severity == Severity.ERROR for i in issues)

    stats = Stats(
        extra={
            "total_issues": len(issues),
            "errors_count": len(diag.errors),
            "warnings_count": len(diag.warnings),
        }
    )

    return ResultEnvelope(
        success=not has_error,
        diagnostics=diag,
        guarantees_applied=["13_UNIVERSAL_GATES_VERIFIED"],
        stats=stats,
    )


def xlsx_diff(
    original_ref: Union[str, FileRef, Dict[str, Any], Path],
    modified_ref: Union[str, FileRef, Dict[str, Any], Path],
    file_store: Optional[FileStore] = None,
) -> ResultEnvelope:
    """So sánh sai lệch cấu trúc giữa 2 file Excel."""
    diag = Diagnostics(engine=Engine.XLSX)

    try:
        path_orig = _resolve_file(original_ref, file_store)
        path_mod = _resolve_file(modified_ref, file_store)
        wb_orig = openpyxl.load_workbook(path_orig, data_only=False)
        wb_mod = openpyxl.load_workbook(path_mod, data_only=False)
    except Exception as exc:
        diag.add_issue(
            Issue(
                code="E-XLSX-DIFF-LOAD-FAILED",
                severity=Severity.ERROR,
                engine=Engine.XLSX,
                message=f"Lỗi khi đọc file để đối soát: {exc}",
            )
        )
        return ResultEnvelope(success=False, diagnostics=diag)

    report, issues = XlsxStructuralDiffer.diff(wb_orig, wb_mod)

    for iss in issues:
        diag.add_issue(iss)

    has_error = any(i.severity == Severity.ERROR for i in issues)

    stats = Stats(
        extra={"diff_report": report.model_dump()},
    )

    return ResultEnvelope(
        success=not has_error,
        diagnostics=diag,
        guarantees_applied=["STRUCTURAL_DIFF_VERIFIED"],
        stats=stats,
    )


def register_xlsx_validate_tools(registry: ToolRegistry) -> None:
    """Đăng ký các MCP tool xlsx.validate và xlsx.diff vào ToolRegistry."""

    @registry.register(
        name="xlsx.validate",
        description="Kiểm tra chất lượng bảng tính Excel qua 13 Universal Gates (UG-01..13).",
        input_model=ValidateInput,
    )
    def handle_validate(
        file_ref: Union[str, Dict[str, Any]],
        template_inventory: Optional[Dict[str, Any]] = None,
    ) -> ResultEnvelope:
        return xlsx_validate(
            file_ref_or_path=file_ref,
            template_inventory=template_inventory,
            file_store=registry.file_store,
        )

    @registry.register(
        name="xlsx.diff",
        description="So sánh sai lệch cấu trúc và hồi quy lỗi giữa 2 workbook Excel.",
        input_model=DiffInput,
    )
    def handle_diff(
        original_ref: Union[str, Dict[str, Any]],
        modified_ref: Union[str, Dict[str, Any]],
    ) -> ResultEnvelope:
        return xlsx_diff(
            original_ref=original_ref,
            modified_ref=modified_ref,
            file_store=registry.file_store,
        )

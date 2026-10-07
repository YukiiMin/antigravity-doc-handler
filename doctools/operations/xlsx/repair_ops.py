"""
doctools.operations.xlsx.repair_ops — Thao tác MCP tự động sửa chữa bảng tính Excel (xlsx.repair).
Tuân thủ FR-16, D-02 của Foundation Plan v1.1:
- Khôi phục cấu hình tính toán, sửa chữa [Content_Types].xml và lọc ký tự bất hợp pháp.
"""

from __future__ import annotations
import io
import os
from pathlib import Path
from typing import Any, Dict, Optional, Union
from pydantic import BaseModel, ConfigDict

from doctools.contract.envelope import Diagnostics, FileRef, ResultEnvelope, Stats
from doctools.contract.issues import Engine, Issue, Severity
from doctools.core.xlsx.repair.workbook_repairer import XlsxWorkbookRepairer
from doctools.infra.file_store import FileStore
from doctools.registry import ToolRegistry


class RepairInput(BaseModel):
    """Schema đầu vào cho MCP tool xlsx.repair."""
    model_config = ConfigDict(extra="ignore")

    file_ref: Union[str, Dict[str, Any]]
    output_path: Optional[str] = None


def _resolve_file(
    input_val: Union[str, FileRef, Dict[str, Any], Path],
    file_store: Optional[FileStore] = None,
) -> Path:
    """Phân giải FileRef, URI hoặc chuỗi đường dẫn."""
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


def xlsx_repair(
    file_ref_or_path: Union[str, FileRef, Dict[str, Any], Path],
    output_path: Optional[str] = None,
    file_store: Optional[FileStore] = None,
) -> ResultEnvelope:
    """Sửa chữa hỏng hóc trong cấu trúc gói OpenXML Excel."""
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

    repairer = XlsxWorkbookRepairer()
    repaired_bytes, repair_issues = repairer.repair(real_path)

    for iss in repair_issues:
        diag.add_issue(iss)

    if any(i.severity == Severity.ERROR for i in repair_issues):
        return ResultEnvelope(success=False, diagnostics=diag)

    fs = file_store or FileStore()
    _XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    out_fileref: Optional[FileRef] = None

    try:
        if output_path is not None:
            dest = Path(output_path).resolve()
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(repaired_bytes)
            out_fileref = fs.store_file(dest, mime=_XLSX_MIME, engine="xlsx")
        else:
            out_fileref = fs.store_bytes(
                data=repaired_bytes,
                mime=_XLSX_MIME,
                engine="xlsx",
                filename_hint=f"repaired_{real_path.name}",
            )
    except Exception as exc:
        diag.add_issue(
            Issue(
                code="E-XLSX-REPAIR-SAVE-FAILED",
                severity=Severity.ERROR,
                engine=Engine.XLSX,
                message=f"Lỗi khi lưu workbook sau sửa chữa: {exc}",
            )
        )
        return ResultEnvelope(success=False, diagnostics=diag)

    stats = Stats(
        extra={
            "repaired_issues_count": len(repair_issues),
            "repaired_actions": [iss.code for iss in repair_issues],
        }
    )

    return ResultEnvelope(
        success=True,
        file_ref=out_fileref,
        diagnostics=diag,
        guarantees_applied=["STRUCTURE_REPAIRED"],
        stats=stats,
    )


def register_xlsx_repair_tools(registry: ToolRegistry) -> None:
    """Đăng ký MCP tool xlsx.repair vào ToolRegistry."""

    @registry.register(
        name="xlsx.repair",
        description="Tự động sửa chữa các lỗi cấu trúc package OpenXML, khôi phục thẻ calcPr và lọc ký tự bất hợp pháp.",
        input_model=RepairInput,
    )
    def handle_repair(
        file_ref: Union[str, Dict[str, Any]],
        output_path: Optional[str] = None,
    ) -> ResultEnvelope:
        return xlsx_repair(file_ref_or_path=file_ref, output_path=output_path, file_store=registry.file_store)

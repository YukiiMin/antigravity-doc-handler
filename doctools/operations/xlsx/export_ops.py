"""
doctools.operations.xlsx.export_ops — Thao tác MCP xuất file Excel 97-2003 (xlsx.export_legacy_xls).
Tuân thủ FR-17, D-02 của Foundation Plan v1.1:
- Xuất bảng tính sang định dạng cổ điển .xls (BIFF8) qua Excel COM hoặc LibreOffice.
- Cấp phát FileRef và ghi nhận kết quả vào ResultEnvelope chuẩn.
"""

from __future__ import annotations
import os
from pathlib import Path
from typing import Any, Dict, Optional, Union
from pydantic import BaseModel, ConfigDict

from doctools.contract.envelope import Diagnostics, FileRef, ResultEnvelope, Stats
from doctools.contract.issues import Engine, Issue, Severity
from doctools.core.xlsx.export.legacy_exporter import XlsxLegacyExporter
from doctools.infra.file_store import FileStore
from doctools.registry import ToolRegistry


class ExportLegacyXlsInput(BaseModel):
    """Schema đầu vào cho MCP tool xlsx.export_legacy_xls."""
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


def xlsx_export_legacy_xls(
    file_ref_or_path: Union[str, FileRef, Dict[str, Any], Path],
    output_path: Optional[str] = None,
    file_store: Optional[FileStore] = None,
) -> ResultEnvelope:
    """Chuyển đổi tệp .xlsx sang tệp Excel cổ điển .xls (Excel 97-2003)."""
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

    exporter = XlsxLegacyExporter()
    out_xls, export_issues = exporter.export_to_xls(xlsx_path=real_path, output_path=output_path)

    for iss in export_issues:
        diag.add_issue(iss)

    if out_xls is None or not out_xls.is_file():
        return ResultEnvelope(success=False, diagnostics=diag)

    fs = file_store or FileStore()
    _XLS_MIME = "application/vnd.ms-excel"

    try:
        out_fileref = fs.store_file(out_xls, mime=_XLS_MIME, engine="xlsx")
    except Exception:
        out_fileref = FileRef.from_path(out_xls)

    stats = Stats(
        extra={
            "output_path": str(out_xls),
            "output_size_bytes": out_xls.stat().st_size,
        }
    )

    return ResultEnvelope(
        success=True,
        file_ref=out_fileref,
        diagnostics=diag,
        guarantees_applied=["LEGACY_BIFF8_EXPORTED"],
        stats=stats,
    )


def register_xlsx_export_tools(registry: ToolRegistry) -> None:
    """Đăng ký MCP tool xlsx.export_legacy_xls vào ToolRegistry."""

    @registry.register(
        name="xlsx.export_legacy_xls",
        description="Xuất tệp Excel hiện đại (.xlsx) sang định dạng cổ điển .xls (Excel 97-2003) qua Excel COM hoặc LibreOffice.",
        input_model=ExportLegacyXlsInput,
    )
    def handle_export(
        file_ref: Union[str, Dict[str, Any]],
        output_path: Optional[str] = None,
    ) -> ResultEnvelope:
        return xlsx_export_legacy_xls(
            file_ref_or_path=file_ref,
            output_path=output_path,
            file_store=registry.file_store,
        )

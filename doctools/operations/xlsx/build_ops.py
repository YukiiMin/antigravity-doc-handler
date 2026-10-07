"""
doctools.operations.xlsx.build_ops — Thao tác MCP dựng bảng tính từ đặc tả XlsxSpec (xlsx.build).
Tuân thủ Path B, FR-08, FR-15 của Foundation Plan v1.1:
- Dựng bảng tính mới từ JSON đặc tả thuần XlsxSpec.
- Tự động sinh DrawingML charts (Bar, Column, Line, Pie) native và format styling.
"""

from __future__ import annotations
import io
import os
from pathlib import Path
from typing import Any, Dict, Optional, Union
from pydantic import BaseModel, ConfigDict

from doctools.contract.envelope import Diagnostics, FileRef, ResultEnvelope, Stats
from doctools.contract.issues import Engine, Issue, Severity
from doctools.contract.xlsx.spec import XlsxSpec
from doctools.core.xlsx.build.spec_builder import XlsxSpecBuilder
from doctools.infra.file_store import FileStore
from doctools.registry import ToolRegistry


class BuildInput(BaseModel):
    """Schema đầu vào cho MCP tool xlsx.build."""
    model_config = ConfigDict(extra="ignore")

    spec: Union[Dict[str, Any], XlsxSpec]
    output_path: Optional[str] = None


def xlsx_build(
    spec: Union[XlsxSpec, Dict[str, Any]],
    output_path: Optional[str] = None,
    file_store: Optional[FileStore] = None,
) -> ResultEnvelope:
    """Dựng workbook hoàn chỉnh từ đặc tả XlsxSpec."""
    diag = Diagnostics(engine=Engine.XLSX)

    if isinstance(spec, dict):
        try:
            parsed_spec = XlsxSpec.model_validate(spec)
        except Exception as exc:
            diag.add_issue(
                Issue(
                    code="E-XLSX-SPEC-INVALID",
                    severity=Severity.ERROR,
                    engine=Engine.XLSX,
                    message=f"XlsxSpec không hợp lệ: {exc}",
                )
            )
            return ResultEnvelope(success=False, diagnostics=diag)
    else:
        parsed_spec = spec

    builder = XlsxSpecBuilder()
    wb, build_issues = builder.build(parsed_spec)

    for iss in build_issues:
        diag.add_issue(iss)

    if any(i.severity == Severity.ERROR for i in build_issues):
        return ResultEnvelope(success=False, diagnostics=diag)

    fs = file_store or FileStore()
    _XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    out_fileref: Optional[FileRef] = None

    try:
        if output_path is not None:
            dest = Path(output_path).resolve()
            dest.parent.mkdir(parents=True, exist_ok=True)
            wb.save(str(dest))
            out_fileref = fs.store_file(dest, mime=_XLSX_MIME, engine="xlsx")
        else:
            buf = io.BytesIO()
            wb.save(buf)
            buf.seek(0)
            hint_name = parsed_spec.output_filename_hint or "built_workbook.xlsx"
            out_fileref = fs.store_bytes(
                data=buf.getvalue(),
                mime=_XLSX_MIME,
                engine="xlsx",
                filename_hint=hint_name,
            )
    except Exception as exc:
        diag.add_issue(
            Issue(
                code="E-XLSX-BUILD-SAVE-FAILED",
                severity=Severity.ERROR,
                engine=Engine.XLSX,
                message=f"Lỗi khi lưu workbook dựng từ spec: {exc}",
            )
        )
        return ResultEnvelope(success=False, diagnostics=diag)

    total_cells = sum(len(s.cells) + sum(len(t.rows) * max(len(t.headers), 1) for t in s.tables) for s in parsed_spec.sheets)
    total_charts = sum(len(s.charts) for s in parsed_spec.sheets)

    stats = Stats(
        elements_processed=total_cells,
        extra={
            "sheets_count": len(wb.sheetnames),
            "sheets": wb.sheetnames,
            "charts_count": total_charts,
        },
    )

    return ResultEnvelope(
        success=True,
        file_ref=out_fileref,
        diagnostics=diag,
        guarantees_applied=["BUILT_FROM_SPEC", "NATIVE_DRAWINGML_CHARTS"],
        stats=stats,
    )


def register_xlsx_build_tools(registry: ToolRegistry) -> None:
    """Đăng ký MCP tool xlsx.build vào ToolRegistry."""

    @registry.register(
        name="xlsx.build",
        description="Khởi tạo bảng tính mới từ JSON XlsxSpec kèm định dạng design tokens và biểu đồ DrawingML native.",
        input_model=BuildInput,
    )
    def handle_build(
        spec: Union[Dict[str, Any], XlsxSpec],
        output_path: Optional[str] = None,
    ) -> ResultEnvelope:
        return xlsx_build(spec=spec, output_path=output_path, file_store=registry.file_store)

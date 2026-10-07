"""
doctools.operations.xlsx.recalc_ops — Thao tác MCP tái tính toán bảng tính (xlsx.recalc).
Tuân thủ FR-10, FR-28, D-12 của Foundation Plan v1.1:
- Tái tính toán công thức qua Windows Excel COM, LibreOffice, hoặc lxml Cache Writer.
- Đảm bảo tính nhất quán của ResultEnvelope và lưu trữ an toàn trong FileStore.
"""

from __future__ import annotations
import os
from pathlib import Path
import shutil
from typing import Any, Dict, Literal, Optional, Union
from pydantic import BaseModel, ConfigDict

from doctools.contract.envelope import Diagnostics, FileRef, ResultEnvelope, Stats
from doctools.contract.issues import Engine, Issue, Severity
from doctools.core.xlsx.recalc.recalc_engine import RecalcEngine
from doctools.infra.file_store import FileStore
from doctools.registry import ToolRegistry


class RecalcInput(BaseModel):
    """Schema đầu vào cho MCP tool xlsx.recalc."""
    model_config = ConfigDict(extra="ignore")

    file_ref: Union[str, Dict[str, Any]]
    method: Literal["auto", "excel_com", "libreoffice", "cache_writer"] = "auto"
    cached_values: Optional[Dict[str, Dict[str, Any]]] = None
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


def xlsx_recalc(
    file_ref_or_path: Union[str, FileRef, Dict[str, Any], Path],
    method: Literal["auto", "excel_com", "libreoffice", "cache_writer"] = "auto",
    cached_values: Optional[Dict[str, Dict[str, Any]]] = None,
    output_path: Optional[str] = None,
    file_store: Optional[FileStore] = None,
) -> ResultEnvelope:
    """Tái tính toán công thức bảng tính Excel."""
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

    fs = file_store or FileStore()
    _XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    # Chuẩn bị file để xử lý
    if output_path is not None:
        target_path = Path(output_path).resolve()
        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(real_path, target_path)
    else:
        # Tạo bản sao tạm để tránh ghi đè ngoài ý muốn
        temp_dir = Path(fs.base_dir) / "recalc_tmp"
        temp_dir.mkdir(parents=True, exist_ok=True)
        target_path = temp_dir / real_path.name
        shutil.copyfile(real_path, target_path)

    engine = RecalcEngine()
    result = engine.recalculate(
        xlsx_path=target_path,
        method=method,
        cached_values=cached_values,
    )

    for iss in result.issues:
        diag.add_issue(iss)

    if not result.success:
        return ResultEnvelope(success=False, diagnostics=diag)

    # Lưu và cấp phát FileRef
    if output_path is not None:
        out_fileref = fs.store_file(target_path, mime=_XLSX_MIME, engine="xlsx")
    else:
        out_fileref = fs.store_bytes(
            data=target_path.read_bytes(),
            mime=_XLSX_MIME,
            engine="xlsx",
            filename_hint=f"recalc_{real_path.name}",
        )

    stats = Stats(
        extra={
            "method_used": result.method_used,
            "target_path": str(target_path),
        }
    )

    return ResultEnvelope(
        success=True,
        file_ref=out_fileref,
        diagnostics=diag,
        guarantees_applied=["RECALCULATED", "CACHE_INJECTED"],
        stats=stats,
    )


def register_xlsx_recalc_tools(registry: ToolRegistry) -> None:
    """Đăng ký MCP tool xlsx.recalc vào ToolRegistry."""

    @registry.register(
        name="xlsx.recalc",
        description="Tái tính toán công thức Excel qua Excel COM, LibreOffice hoặc tiêm giá trị cache <v>.",
        input_model=RecalcInput,
    )
    def handle_recalc(
        file_ref: Union[str, Dict[str, Any]],
        method: Literal["auto", "excel_com", "libreoffice", "cache_writer"] = "auto",
        cached_values: Optional[Dict[str, Dict[str, Any]]] = None,
        output_path: Optional[str] = None,
    ) -> ResultEnvelope:
        return xlsx_recalc(
            file_ref_or_path=file_ref,
            method=method,
            cached_values=cached_values,
            output_path=output_path,
            file_store=registry.file_store,
        )

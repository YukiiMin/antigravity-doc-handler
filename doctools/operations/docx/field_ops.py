"""
doctools.operations.docx.field_ops
MCP Tool Operation for dynamic fields and TOC discovery/updates (docx.update_fields).
"""

from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, Literal, Optional, Union
import urllib.parse

from doctools.contract import (
    Diagnostics,
    Engine,
    FileRef,
    Issue,
    ResultEnvelope,
    Severity,
    Stats,
)
from doctools.core.docx.fields import field_manager
from doctools.infra.file_store import FileStore

_DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


def _resolve_file_input(
    input_val: Union[str, FileRef, Dict[str, Any], Path],
    file_store: FileStore,
) -> tuple[Optional[Path], Optional[Issue]]:
    """Resolves input file reference or path into a concrete Path on disk."""
    if isinstance(input_val, dict) and "uri" in input_val:
        input_val = FileRef(**input_val)

    if isinstance(input_val, FileRef):
        return file_store.resolve(input_val), None

    if isinstance(input_val, Path):
        return input_val.resolve(), None

    val_str = str(input_val).strip()
    if val_str.startswith("resource://"):
        return file_store.resolve(val_str), None

    if val_str.startswith("file://"):
        parsed = urllib.parse.urlparse(val_str)
        p = urllib.parse.unquote(parsed.path)
        if len(p) > 2 and p[0] == "/" and p[2] == ":":
            p = p[1:]
        return Path(p).resolve(), None

    path_obj = Path(val_str).resolve()
    if path_obj.is_file():
        return path_obj, None

    return None, Issue(
        code="E-FILE-NOT-FOUND",
        severity=Severity.ERROR,
        engine=Engine.DOCX,
        message=f"Cannot resolve document input: '{input_val}'.",
    )


def docx_update_fields(
    file_ref_or_path: Union[str, FileRef, Dict[str, Any], Path],
    field_update: Literal["auto", "none", "update_on_open"] = "auto",
    toc_mode: Literal["with_page_numbers", "no_page_numbers"] = "with_page_numbers",
    output_path: Optional[Union[str, Path]] = None,
    file_store: Optional[FileStore] = None,
) -> ResultEnvelope:
    """Discovers dynamic fields and applies update policies (w:updateFields in settings.xml)."""
    fs = file_store or FileStore()
    diag = Diagnostics(engine=Engine.DOCX)

    resolved, err = _resolve_file_input(file_ref_or_path, fs)
    if err is not None:
        diag.add_issue(err)
        return ResultEnvelope(success=False, diagnostics=diag)

    raw_bytes = resolved.read_bytes()
    out_bytes, issues, guarantees, stats_data = field_manager.apply_update_policy(
        raw_bytes=raw_bytes,
        field_update=field_update,
        toc_mode=toc_mode,
    )

    for iss in issues:
        diag.add_issue(iss)

    out_fileref: Optional[FileRef] = None
    if output_path is not None:
        dest = Path(output_path).resolve()
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(out_bytes)
        out_fileref = fs.store_file(dest, mime=_DOCX_MIME, engine="docx")
    else:
        out_fileref = fs.store_bytes(
            data=out_bytes,
            mime=_DOCX_MIME,
            engine="docx",
            filename_hint=f"fields_{resolved.name}",
        )

    stats = Stats(
        elements_processed=stats_data.get("fields_detected", 0),
        extra=stats_data,
    )

    return ResultEnvelope(
        success=True,
        file_ref=out_fileref,
        diagnostics=diag,
        guarantees_applied=guarantees,
        stats=stats,
    )


def register_field_ops(registry: Any) -> None:
    """Registers docx.update_fields tool into ToolRegistry."""

    @registry.register(
        name="docx.update_fields",
        description="Phát hiện trường động (TOC, PAGEREF) và quản lý cờ tự động cập nhật w:updateFields khi mở tệp Word.",
    )
    def _fields_tool(
        file_ref: Any,
        field_update: str = "auto",
        toc_mode: str = "with_page_numbers",
        output_path: Optional[str] = None,
    ) -> ResultEnvelope:
        return docx_update_fields(
            file_ref_or_path=file_ref,
            field_update=field_update,  # type: ignore[arg-type]
            toc_mode=toc_mode,  # type: ignore[arg-type]
            output_path=output_path,
            file_store=registry.file_store,
        )

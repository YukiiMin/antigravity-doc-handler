"""
doctools.operations.docx.patch_ops
MCP Tool Operation for in-place document modification (docx.patch).
"""

from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
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
from doctools.contract.docx.patch import PatchOp, PatchSpec
from doctools.core.docx.patch import docx_patcher
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


def docx_patch(
    file_ref_or_path: Union[str, FileRef, Dict[str, Any], Path],
    operations: Union[List[Dict[str, Any]], PatchSpec, List[PatchOp]],
    output_path: Optional[Union[str, Path]] = None,
    file_store: Optional[FileStore] = None,
) -> ResultEnvelope:
    """Applies declarative patch operations to modify an existing DOCX document."""
    fs = file_store or FileStore()
    diag = Diagnostics(engine=Engine.DOCX)

    resolved, err = _resolve_file_input(file_ref_or_path, fs)
    if err is not None:
        diag.add_issue(err)
        return ResultEnvelope(success=False, diagnostics=diag)

    patch_res = docx_patcher.patch(doc_input=resolved, patch_spec=operations)

    for iss in patch_res.issues:
        diag.add_issue(iss)

    if any(i.severity == Severity.ERROR for i in patch_res.issues):
        return ResultEnvelope(success=False, diagnostics=diag)

    # Store patched result
    out_fileref: Optional[FileRef] = None
    if output_path is not None:
        dest = Path(output_path).resolve()
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(patch_res.docx_bytes)
        out_fileref = fs.store_file(dest, mime=_DOCX_MIME, engine="docx")
    else:
        out_fileref = fs.store_bytes(
            data=patch_res.docx_bytes,
            mime=_DOCX_MIME,
            engine="docx",
            filename_hint=f"patched_{resolved.name}",
        )

    stats = Stats(
        elements_processed=patch_res.stats.get("applied_ops", 0),
        extra=patch_res.stats,
    )

    return ResultEnvelope(
        success=True,
        file_ref=out_fileref,
        diagnostics=diag,
        guarantees_applied=patch_res.guarantees_applied,
        stats=stats,
    )


def register_patch_ops(registry: Any) -> None:
    """Registers docx.patch tool into ToolRegistry."""

    @registry.register(
        name="docx.patch",
        description="Sửa đổi tài liệu Word tại chỗ bằng thao tác khai báo, bảo toàn định dạng run và rào chắn OOXML.",
    )
    def _patch_tool(
        file_ref: Any,
        operations: List[Dict[str, Any]],
        output_path: Optional[str] = None,
    ) -> ResultEnvelope:
        return docx_patch(
            file_ref_or_path=file_ref,
            operations=operations,
            output_path=output_path,
            file_store=registry.file_store,
        )

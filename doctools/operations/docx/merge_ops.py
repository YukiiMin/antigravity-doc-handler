"""
doctools.operations.docx.merge_ops
MCP Tool Operation for multi-document merging and appendix stitching (docx.merge).
"""

from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Union
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
from doctools.core.docx.merge import StyleConflictPolicy, docx_merger
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


def docx_merge(
    base_ref_or_path: Union[str, FileRef, Dict[str, Any], Path],
    parts: List[Union[str, FileRef, Dict[str, Any], Path]],
    style_conflict_policy: StyleConflictPolicy = "master_wins",
    output_path: Optional[Union[str, Path]] = None,
    file_store: Optional[FileStore] = None,
) -> ResultEnvelope:
    """Merges appendix/part documents into a base document."""
    fs = file_store or FileStore()
    diag = Diagnostics(engine=Engine.DOCX)

    base_resolved, base_err = _resolve_file_input(base_ref_or_path, fs)
    if base_err is not None:
        diag.add_issue(base_err)
        return ResultEnvelope(success=False, diagnostics=diag)

    part_paths: List[Path] = []
    for idx, p_item in enumerate(parts):
        p_res, p_err = _resolve_file_input(p_item, fs)
        if p_err is not None:
            diag.add_issue(p_err)
            return ResultEnvelope(success=False, diagnostics=diag)
        part_paths.append(p_res)

    merge_res = docx_merger.merge(
        base_input=base_resolved,
        parts=part_paths,
        style_conflict_policy=style_conflict_policy,
    )

    for iss in merge_res.issues:
        diag.add_issue(iss)

    if any(i.severity == Severity.ERROR for i in merge_res.issues):
        return ResultEnvelope(success=False, diagnostics=diag)

    # Store output
    out_fileref: Optional[FileRef] = None
    if output_path is not None:
        dest = Path(output_path).resolve()
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(merge_res.docx_bytes)
        out_fileref = fs.store_file(dest, mime=_DOCX_MIME, engine="docx")
    else:
        out_fileref = fs.store_bytes(
            data=merge_res.docx_bytes,
            mime=_DOCX_MIME,
            engine="docx",
            filename_hint=f"merged_{base_resolved.name}",
        )

    stats = Stats(
        elements_processed=merge_res.stats.get("appended_parts", 0),
        extra=merge_res.stats,
    )

    return ResultEnvelope(
        success=True,
        file_ref=out_fileref,
        diagnostics=diag,
        guarantees_applied=merge_res.guarantees_applied,
        stats=stats,
    )


def register_merge_ops(registry: Any) -> None:
    """Registers docx.merge tool into ToolRegistry."""

    @registry.register(
        name="docx.merge",
        description="Ghép các tệp tài liệu con/phụ lục vào tài liệu chính, giải quyết xung đột style và bảo vệ bố cục.",
    )
    def _merge_tool(
        base_ref: Any,
        parts: List[Any],
        style_conflict_policy: str = "master_wins",
        output_path: Optional[str] = None,
    ) -> ResultEnvelope:
        return docx_merge(
            base_ref_or_path=base_ref,
            parts=parts,
            style_conflict_policy=style_conflict_policy,  # type: ignore[arg-type]
            output_path=output_path,
            file_store=registry.file_store,
        )

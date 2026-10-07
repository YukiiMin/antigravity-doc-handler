"""
doctools.operations.docx.inspect_ops
MCP Tool Operations for document inspection and quality gate validation:
- docx.inspect_structure: Parses document tree with stable anchors.
- docx.validate: Runs universal quality gates DG-01 to DG-06.
"""

from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, Optional, Union
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
from doctools.core.docx.inspect import structure_inspector
from doctools.gates.docx import docx_quality_gates
from doctools.infra.file_store import FileStore


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


def docx_inspect_structure(
    file_ref_or_path: Union[str, FileRef, Dict[str, Any], Path],
    file_store: Optional[FileStore] = None,
) -> ResultEnvelope:
    """Extracts hierarchical structure tree with anchors for AI inspection."""
    fs = file_store or FileStore()
    diag = Diagnostics(engine=Engine.DOCX)

    resolved, err = _resolve_file_input(file_ref_or_path, fs)
    if err is not None:
        diag.add_issue(err)
        return ResultEnvelope(success=False, diagnostics=diag)

    if not resolved.is_file():
        diag.add_issue(Issue(
            code="E-FILE-NOT-FOUND",
            severity=Severity.ERROR,
            engine=Engine.DOCX,
            message=f"Target document does not exist: {resolved}",
        ))
        return ResultEnvelope(success=False, diagnostics=diag)

    try:
        tree = structure_inspector.inspect(resolved)
        stats = Stats(
            elements_processed=tree["stats"]["paragraph_count"] + tree["stats"]["table_count"],
            extra={"stats": tree["stats"], "structure": tree},
        )
        return ResultEnvelope(
            success=True,
            diagnostics=diag,
            stats=stats,
        )
    except Exception as exc:
        diag.add_issue(Issue(
            code="E-DOCX-INSPECT-FAILED",
            severity=Severity.ERROR,
            engine=Engine.DOCX,
            message=f"Failed to inspect document structure: {exc}",
        ))
        return ResultEnvelope(success=False, diagnostics=diag)


def docx_validate(
    file_ref_or_path: Union[str, FileRef, Dict[str, Any], Path],
    file_store: Optional[FileStore] = None,
) -> ResultEnvelope:
    """Executes quality gates DG-01 through DG-06 against the target document."""
    fs = file_store or FileStore()
    diag = Diagnostics(engine=Engine.DOCX)

    resolved, err = _resolve_file_input(file_ref_or_path, fs)
    if err is not None:
        diag.add_issue(err)
        return ResultEnvelope(success=False, diagnostics=diag)

    issues = docx_quality_gates.validate(resolved)
    for iss in issues:
        diag.add_issue(iss)

    has_error = any(i.severity == Severity.ERROR for i in issues)
    stats = Stats(
        elements_processed=len(issues),
        extra={
            "total_issues": len(issues),
            "errors": len([i for i in issues if i.severity == Severity.ERROR]),
            "warnings": len([i for i in issues if i.severity == Severity.WARNING]),
        },
    )

    return ResultEnvelope(
        success=not has_error,
        diagnostics=diag,
        stats=stats,
    )


def register_inspect_ops(registry: Any) -> None:
    """Registers docx.inspect_structure and docx.validate tools into ToolRegistry."""

    @registry.register(
        name="docx.inspect_structure",
        description="Đọc cây cấu trúc tài liệu Word với hệ tọa độ anchor ổn định để AI phân tích và sửa đổi.",
    )
    def _inspect_tool(file_ref: Any) -> ResultEnvelope:
        return docx_inspect_structure(file_ref_or_path=file_ref, file_store=registry.file_store)

    @registry.register(
        name="docx.validate",
        description="Kiểm tra chất lượng và tính hợp lệ OpenXML qua các rào chắn DG-01 đến DG-06.",
    )
    def _validate_tool(file_ref: Any) -> ResultEnvelope:
        return docx_validate(file_ref_or_path=file_ref, file_store=registry.file_store)

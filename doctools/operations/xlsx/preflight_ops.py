"""
doctools.operations.xlsx.preflight_ops
MCP Tool Operation for XLSX preflight analysis (xlsx.preflight).
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
from doctools.core.xlsx.preflight import preflight_scanner
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
        engine=Engine.XLSX,
        message=f"Cannot resolve spreadsheet input: '{input_val}'.",
    )


def xlsx_preflight(
    file_ref_or_path: Union[str, FileRef, Dict[str, Any], Path],
    file_store: Optional[FileStore] = None,
) -> ResultEnvelope:
    """Performs preflight inspection, extracts package inventory, and sets fidelity tier."""
    fs = file_store or FileStore()
    diag = Diagnostics(engine=Engine.XLSX)

    resolved, err = _resolve_file_input(file_ref_or_path, fs)
    if err is not None:
        diag.add_issue(err)
        return ResultEnvelope(success=False, diagnostics=diag)

    scan_res = preflight_scanner.scan(resolved)
    for iss in scan_res.issues:
        diag.add_issue(iss)

    has_error = any(i.severity == Severity.ERROR for i in scan_res.issues)

    stats = Stats(
        elements_processed=len(scan_res.inventory.sheets),
        extra={
            "inventory": scan_res.inventory.model_dump(),
            "fidelity_tier": scan_res.inventory.fidelity_tier,
        },
    )

    return ResultEnvelope(
        success=not has_error,
        diagnostics=diag,
        guarantees_applied=scan_res.guarantees_applied,
        stats=stats,
    )


def register_preflight_ops(registry: Any) -> None:
    """Registers xlsx.preflight tool into ToolRegistry."""

    @registry.register(
        name="xlsx.preflight",
        description="Quét toàn diện package Excel, lập Inventory cấu trúc và xác định Fidelity Tier (T1..T4).",
    )
    def _preflight_tool(file_ref: Any) -> ResultEnvelope:
        return xlsx_preflight(file_ref_or_path=file_ref, file_store=registry.file_store)

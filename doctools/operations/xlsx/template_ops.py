"""
doctools.operations.xlsx.template_ops — Các thao tác quản lý template và đăng ký MCP tool cho XLSX.
Cung cấp các hàm dịch vụ bọc ResultEnvelope:
- xlsx_register_template: Đăng ký template vào kho với manifest
- xlsx_lint_template: Kiểm định tĩnh template Excel và đối chiếu manifest
- xlsx_list_templates: Liệt kê danh sách template đã đăng ký
- register_xlsx_template_tools: Đăng ký vào ToolRegistry trung tâm
"""

from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import urllib.parse
from pydantic import BaseModel, ConfigDict, Field

from doctools.contract.envelope import Diagnostics, FileRef, ResultEnvelope, Stats
from doctools.contract.issues import Engine, Issue, Severity
from doctools.contract.xlsx.manifest import XlsxTemplateManifest
from doctools.core.xlsx.template.manifest_parser import (
    ManifestParseError,
    parse_manifest,
)
from doctools.core.xlsx.template.template_linter import XlsxTemplateLinter
from doctools.core.xlsx.template.template_registry import (
    XlsxTemplateRegistry,
    get_default_xlsx_template_registry,
)
from doctools.infra.file_store import FileStore
from doctools.registry import ToolRegistry


def _resolve_xlsx_path(
    input_val: Union[str, FileRef, Dict[str, Any], Path],
    file_store: Optional[FileStore] = None,
) -> Path:
    """Phân giải an toàn đầu vào thành Path tuyệt đối trên đĩa."""
    if isinstance(input_val, dict) and "uri" in input_val:
        input_val = FileRef(**input_val)

    if isinstance(input_val, FileRef):
        fs = file_store or FileStore()
        return fs.resolve(input_val)

    if isinstance(input_val, Path):
        return input_val.resolve()

    val_str = str(input_val).strip()
    if val_str.startswith("resource://"):
        fs = file_store or FileStore()
        return fs.resolve(val_str)

    if val_str.startswith("file://"):
        parsed = urllib.parse.urlparse(val_str)
        file_path = urllib.parse.unquote(parsed.path)
        if file_path.startswith("/") and len(file_path) > 2 and file_path[2] == ":":
            file_path = file_path[1:]
        return Path(file_path).resolve()

    return Path(val_str).resolve()


def xlsx_register_template(
    template_ref: Union[str, FileRef, Dict[str, Any], Path],
    manifest: Union[Dict[str, Any], str, Path, XlsxTemplateManifest],
    force_version: Optional[int] = None,
    template_registry: Optional[XlsxTemplateRegistry] = None,
    file_store: Optional[FileStore] = None,
) -> ResultEnvelope:
    """
    Đăng ký template Excel vào kho kèm manifest.
    Thực hiện kiểm tra sha256, chạy Preflight và xác minh các bất biến.
    """
    t_reg = template_registry or get_default_xlsx_template_registry()

    record, issues = t_reg.register(template_ref, manifest, force_version=force_version)

    diag = Diagnostics(engine=Engine.XLSX)
    for issue in issues:
        diag.add_issue(issue)

    if record is None:
        return ResultEnvelope(success=False, diagnostics=diag)

    stats = Stats(
        elements_processed=len(record.manifest.anchors),
        extra={
            "template_id": record.template_id,
            "version": record.version,
            "sha256": record.sha256,
            "reference_sheet": record.manifest.reference_sheet,
            "tier": (
                record.inventory.fidelity_tier.value
                if hasattr(record.inventory.fidelity_tier, "value")
                else str(record.inventory.fidelity_tier)
            ),
        },
    )

    return ResultEnvelope(
        success=True,
        file_ref=record.file_ref,
        diagnostics=diag,
        guarantees_applied=["template_immutable_stored", "manifest_verified", "sha256_tracked"],
        stats=stats,
    )


def xlsx_lint_template(
    template_ref: Union[str, FileRef, Dict[str, Any], Path],
    manifest: Optional[Union[Dict[str, Any], str, Path, XlsxTemplateManifest]] = None,
    file_store: Optional[FileStore] = None,
) -> ResultEnvelope:
    """Kiểm tra tĩnh template Excel và đối chiếu manifest nếu được cung cấp."""
    try:
        resolved_path = _resolve_xlsx_path(template_ref, file_store)
        if not resolved_path.exists():
            diag = Diagnostics(engine=Engine.XLSX)
            diag.add_issue(Issue(
                code="E-TPL-FILE-NOT-FOUND",
                severity=Severity.ERROR,
                engine=Engine.XLSX,
                message=f"Tệp template không tồn tại: {resolved_path}",
            ))
            return ResultEnvelope(success=False, diagnostics=diag)

        parsed_manifest: Optional[XlsxTemplateManifest] = None
        if manifest is not None:
            parsed_manifest = parse_manifest(manifest)

        linter = XlsxTemplateLinter()
        report = linter.lint(resolved_path, manifest=parsed_manifest)

        diag = Diagnostics(engine=Engine.XLSX)
        for issue in report.issues:
            diag.add_issue(issue)

        stats = Stats(
            elements_processed=report.stats.get("total_cells_scanned", 0),
            extra={
                "placeholders_found": report.placeholders_found,
                "sheets_scanned": report.sheets_scanned,
                **report.stats,
            },
        )
        return ResultEnvelope(
            success=report.valid,
            file_ref=template_ref if isinstance(template_ref, FileRef) else None,
            diagnostics=diag,
            guarantees_applied=["read_only_inspection", "non_destructive"],
            stats=stats,
        )
    except Exception as exc:
        diag = Diagnostics(engine=Engine.XLSX)
        diag.add_issue(Issue(
            code="E-TPL-LINT-EXCEPTION",
            severity=Severity.ERROR,
            engine=Engine.XLSX,
            message=f"Ngoại lệ khi kiểm định template: {exc}",
        ))
        return ResultEnvelope(success=False, diagnostics=diag)


def xlsx_list_templates(
    template_registry: Optional[XlsxTemplateRegistry] = None,
) -> ResultEnvelope:
    """Liệt kê danh sách các template Excel đã đăng ký trong hệ thống."""
    t_reg = template_registry or get_default_xlsx_template_registry()
    templates = t_reg.list_templates()
    stats = Stats(elements_processed=len(templates), extra={"templates": templates})
    return ResultEnvelope(
        success=True,
        diagnostics=Diagnostics(engine=Engine.XLSX),
        guarantees_applied=["read_only_inventory"],
        stats=stats,
    )


class RegisterTemplateInput(BaseModel):
    model_config = ConfigDict(extra="ignore")
    template_ref: Union[str, Dict[str, Any]]
    manifest: Union[Dict[str, Any], str]
    force_version: Optional[int] = None


class LintTemplateInput(BaseModel):
    model_config = ConfigDict(extra="ignore")
    template_ref: Union[str, Dict[str, Any]]
    manifest: Optional[Union[Dict[str, Any], str]] = None


class ListTemplatesInput(BaseModel):
    model_config = ConfigDict(extra="ignore")


def register_xlsx_template_tools(
    registry: ToolRegistry,
    template_registry: Optional[XlsxTemplateRegistry] = None,
) -> None:
    """Đăng ký các MCP tool liên quan đến template Excel vào ToolRegistry."""
    t_reg = template_registry or get_default_xlsx_template_registry()

    @registry.register(
        name="xlsx.register_template",
        description="Đăng ký một template Excel (.xlsx) kèm manifest vào kho lưu trữ có phiên bản.",
        input_model=RegisterTemplateInput,
    )
    def handle_register(
        template_ref: Union[str, Dict[str, Any]],
        manifest: Union[Dict[str, Any], str],
        force_version: Optional[int] = None,
    ) -> ResultEnvelope:
        return xlsx_register_template(
            template_ref=template_ref,
            manifest=manifest,
            force_version=force_version,
            template_registry=t_reg,
            file_store=registry.file_store,
        )

    @registry.register(
        name="xlsx.lint_template",
        description="Kiểm tra chất lượng tĩnh template Excel và tính nhất quán với manifest.",
        input_model=LintTemplateInput,
    )
    def handle_lint(
        template_ref: Union[str, Dict[str, Any]],
        manifest: Optional[Union[Dict[str, Any], str]] = None,
    ) -> ResultEnvelope:
        return xlsx_lint_template(
            template_ref=template_ref,
            manifest=manifest,
            file_store=registry.file_store,
        )

    @registry.register(
        name="xlsx.list_templates",
        description="Liệt kê toàn bộ các template Excel đã được đăng ký và phiên bản của chúng.",
        input_model=ListTemplatesInput,
    )
    def handle_list() -> ResultEnvelope:
        return xlsx_list_templates(template_registry=t_reg)


"""
doctools.operations.docx.template_ops
Triển khai các nghiệp vụ MCP Tools:
- docx.lint_template (WF-DOCX-01): Kiểm tra template thuần đọc, phát hiện lỗi cú pháp, split tags, dynamic fields.
- docx.normalize_template: Hàn gắn các cụm run Jinja bị băm nhỏ, dọn rác w:proofErr theo Mục 4.14.
- docx.register_template: Đăng ký template vào kho kèm manifest YAML/JSON.
- docx.list_templates: Liệt kê danh mục template hợp lệ trong kho.
- docx.get_template_manifest: Lấy chi tiết slot biến và ràng buộc của template.
"""

from __future__ import annotations
import urllib.parse
from pathlib import Path
from typing import Any, Dict, Optional, Union

from doctools.contract import (
    Diagnostics,
    Engine,
    FileRef,
    Issue,
    Location,
    ResultEnvelope,
    Severity,
    Stats,
)
from doctools.contract.docx.manifest import TemplateManifest
from doctools.core.docx.template import (
    TemplateRegistry,
    get_default_template_registry,
    jinja_normalizer,
    template_linter,
)
from doctools.infra.file_store import FileStore

_DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


def _resolve_input_path(
    input_val: Union[str, FileRef, Dict[str, Any], Path],
    file_store: Optional[FileStore] = None,
) -> Path:
    """Phân giải an toàn đầu vào thành đối tượng Path trên đĩa."""
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
        if len(file_path) > 2 and file_path[0] == "/" and file_path[2] == ":":
            file_path = file_path[1:]
        return Path(file_path).resolve()

    return Path(val_str).resolve()


def docx_lint_template(
    template_ref: Union[str, FileRef, Dict[str, Any], Path],
    file_store: Optional[FileStore] = None,
) -> ResultEnvelope:
    """Kiểm định template thuần đọc và trả về ResultEnvelope kèm issues."""
    fs = file_store or FileStore()
    try:
        resolved_path = _resolve_input_path(template_ref, fs)
        if not resolved_path.is_file():
            diag = Diagnostics(engine=Engine.DOCX)
            diag.add_issue(Issue(
                code="E-FILE-NOT-FOUND",
                severity=Severity.ERROR,
                engine=Engine.DOCX,
                message=f"Tệp template không tồn tại: {resolved_path}",
                location=Location(part=str(resolved_path)),
            ))
            return ResultEnvelope(success=False, diagnostics=diag)

        report = template_linter.lint(resolved_path)
        diag = Diagnostics(engine=Engine.DOCX)
        for issue in report.issues:
            diag.add_issue(issue)

        stats = Stats(
            elements_processed=report.stats.get("paragraphs_scanned", 0),
            extra={"variables": report.variables, "fields_detected": report.fields_detected, **report.stats},
        )
        return ResultEnvelope(
            success=report.valid,
            file_ref=template_ref if isinstance(template_ref, FileRef) else None,
            diagnostics=diag,
            guarantees_applied=["read_only_template_inspection"],
            stats=stats,
        )
    except Exception as exc:
        diag = Diagnostics(engine=Engine.DOCX)
        diag.add_issue(Issue(
            code="E-DOCX-LINT-EXCEPTION",
            severity=Severity.ERROR,
            engine=Engine.DOCX,
            message=f"Ngoại lệ khi kiểm định template: {str(exc)}",
        ))
        return ResultEnvelope(success=False, diagnostics=diag)


def docx_normalize_template(
    template_ref: Union[str, FileRef, Dict[str, Any], Path],
    output_path: Optional[Union[str, Path]] = None,
    file_store: Optional[FileStore] = None,
) -> ResultEnvelope:
    """Hàn gắn các run Jinja bị băm, dọn rác w:proofErr và sinh tệp DOCX chuẩn hóa mới."""
    fs = file_store or FileStore()
    try:
        resolved_path = _resolve_input_path(template_ref, fs)
        if not resolved_path.is_file():
            diag = Diagnostics(engine=Engine.DOCX)
            diag.add_issue(Issue(
                code="E-FILE-NOT-FOUND",
                severity=Severity.ERROR,
                engine=Engine.DOCX,
                message=f"Tệp template không tồn tại: {resolved_path}",
                location=Location(part=str(resolved_path)),
            ))
            return ResultEnvelope(success=False, diagnostics=diag)

        norm_result = jinja_normalizer.normalize(resolved_path)
        diag = Diagnostics(engine=Engine.DOCX)
        for issue in norm_result.issues:
            diag.add_issue(issue)

        out_fileref: Optional[FileRef] = None
        if output_path is not None:
            dest = Path(output_path).resolve()
            dest.parent.mkdir(parents=True, exist_ok=True)
            with open(dest, "wb") as f:
                f.write(norm_result.normalized_bytes)
            out_fileref = fs.store_file(dest, mime=_DOCX_MIME, engine="docx")
        else:
            out_fileref = fs.store_bytes(
                data=norm_result.normalized_bytes,
                mime=_DOCX_MIME,
                engine="docx",
                filename_hint=f"normalized_{resolved_path.name}",
            )

        stats = Stats(
            elements_processed=norm_result.diff_summary.get("paragraphs_modified", 0),
            extra=norm_result.diff_summary,
        )
        return ResultEnvelope(
            success=True,
            file_ref=out_fileref,
            diagnostics=diag,
            guarantees_applied=["runs_consolidated", "proofErr_removed", "xml_space_preserved", "non_destructive_output"],
            stats=stats,
        )
    except Exception as exc:
        diag = Diagnostics(engine=Engine.DOCX)
        diag.add_issue(Issue(
            code="E-DOCX-NORMALIZE-EXCEPTION",
            severity=Severity.ERROR,
            engine=Engine.DOCX,
            message=f"Ngoại lệ khi chuẩn hóa template: {str(exc)}",
        ))
        return ResultEnvelope(success=False, diagnostics=diag)


def docx_register_template(
    template_ref: Union[str, FileRef, Dict[str, Any], Path],
    manifest: Union[Dict[str, Any], str, Path, TemplateManifest],
    force_version: Optional[int] = None,
    template_registry: Optional[TemplateRegistry] = None,
) -> ResultEnvelope:
    """Đăng ký template vào kho kèm manifest, kiểm định tính hợp lệ và sha256."""
    t_reg = template_registry or get_default_template_registry()
    record, issues = t_reg.register(template_ref, manifest, force_version=force_version)

    diag = Diagnostics(engine=Engine.DOCX)
    for issue in issues:
        diag.add_issue(issue)

    if record is None:
        return ResultEnvelope(success=False, diagnostics=diag)

    stats = Stats(
        elements_processed=len(record.manifest.variables),
        extra={
            "template_id": record.template_id,
            "version": record.version,
            "manifest": record.manifest.model_dump(),
        },
    )
    return ResultEnvelope(
        success=True,
        file_ref=record.file_ref,
        diagnostics=diag,
        guarantees_applied=["template_manifest_validated", "sha256_verified"],
        stats=stats,
    )


def docx_list_templates(template_registry: Optional[TemplateRegistry] = None) -> ResultEnvelope:
    """Liệt kê danh sách các template đã đăng ký trong kho."""
    t_reg = template_registry or get_default_template_registry()
    templates = t_reg.list_templates()
    stats = Stats(elements_processed=len(templates), extra={"templates": templates, "count": len(templates)})
    return ResultEnvelope(
        success=True,
        diagnostics=Diagnostics(engine=Engine.DOCX),
        guarantees_applied=["inventory_retrieved"],
        stats=stats,
    )


def docx_get_template_manifest(
    template_id: str,
    version: Optional[int] = None,
    template_registry: Optional[TemplateRegistry] = None,
) -> ResultEnvelope:
    """Trích xuất manifest của template đã đăng ký."""
    t_reg = template_registry or get_default_template_registry()
    rec = t_reg.get(template_id, version=version)
    diag = Diagnostics(engine=Engine.DOCX)
    if not rec:
        diag.add_issue(Issue(
            code="E-DOCX-TPL-NOT-FOUND",
            severity=Severity.ERROR,
            engine=Engine.DOCX,
            message=f"Template '{template_id}' (phiên bản {version or 'latest'}) không tồn tại trong kho.",
        ))
        return ResultEnvelope(success=False, diagnostics=diag)

    stats = Stats(
        elements_processed=len(rec.manifest.variables),
        extra={"template_id": rec.template_id, "version": rec.version, "manifest": rec.manifest.model_dump()},
    )
    return ResultEnvelope(
        success=True,
        file_ref=rec.file_ref,
        diagnostics=diag,
        guarantees_applied=["manifest_retrieved"],
        stats=stats,
    )


def register_template_ops(registry: Any) -> None:
    """Đăng ký các MCP Tools quản lý và chuẩn hóa template DOCX vào Registry."""

    @registry.register(
        name="docx.lint_template",
        description="Kiểm định template DOCX thuần đọc: phát hiện cú pháp Jinja2, split tags, dynamic fields, SSTI.",
    )
    def _lint_tool(template_ref: Any) -> ResultEnvelope:
        return docx_lint_template(template_ref, file_store=registry.file_store)

    @registry.register(
        name="docx.normalize_template",
        description="Hàn gắn các run Jinja bị băm nhỏ, dọn rác w:proofErr và sinh file DOCX chuẩn hóa mới.",
    )
    def _normalize_tool(template_ref: Any, output_path: Optional[str] = None) -> ResultEnvelope:
        return docx_normalize_template(template_ref, output_path=output_path, file_store=registry.file_store)

    @registry.register(
        name="docx.register_template",
        description="Đăng ký template vào kho kèm manifest YAML/JSON: xác thực schema và đối soát sha256.",
    )
    def _reg_tool(template_ref: Any, manifest: Any, force_version: Optional[int] = None) -> ResultEnvelope:
        return docx_register_template(template_ref, manifest, force_version=force_version)

    @registry.register(
        name="docx.list_templates",
        description="Liệt kê danh mục template hợp lệ trong kho.",
    )
    def _list_tool() -> ResultEnvelope:
        return docx_list_templates()

    @registry.register(
        name="docx.get_template_manifest",
        description="Lấy chi tiết manifest, danh mục biến và ràng buộc layout của template.",
    )
    def _manifest_tool(template_id: str, version: Optional[int] = None) -> ResultEnvelope:
        return docx_get_template_manifest(template_id, version=version)

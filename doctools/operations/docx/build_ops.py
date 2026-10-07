"""
doctools.operations.docx.build_ops
MCP Tool Operations for document building:
- docx.render_template: Path A Template rendering with Jinja2 sandboxing and OOXML guards.
- docx.build_document: Unified dispatcher for Path A (Template) and Path B (DocSpec).
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
from doctools.contract.docx.manifest import LayoutPolicy, TemplateManifest
from doctools.core.docx.build import jinja_renderer
from doctools.core.docx.template import (
    TemplateRegistry,
    get_default_template_registry,
)
from doctools.infra.file_store import FileStore

_DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


def _resolve_template_input(
    template_ref_or_id: Union[str, FileRef, Dict[str, Any], Path],
    file_store: FileStore,
    template_registry: TemplateRegistry,
) -> tuple[Optional[Path], Optional[TemplateManifest], Optional[Issue]]:
    """Resolves template file path and optional manifest from FileRef or registered ID."""
    manifest: Optional[TemplateManifest] = None

    if isinstance(template_ref_or_id, str) and not template_ref_or_id.startswith(("file://", "resource://", "/", "\\")):
        # Check if it's a registered template_id
        rec = template_registry.get(template_ref_or_id)
        if rec is not None:
            manifest = rec.manifest
            resolved = file_store.resolve(rec.file_ref)
            return resolved, manifest, None

    # Resolve from FileRef / URI / Path
    input_val = template_ref_or_id
    if isinstance(input_val, dict) and "uri" in input_val:
        input_val = FileRef(**input_val)

    if isinstance(input_val, FileRef):
        resolved = file_store.resolve(input_val)
        return resolved, manifest, None

    if isinstance(input_val, Path):
        return input_val.resolve(), manifest, None

    val_str = str(input_val).strip()
    if val_str.startswith("resource://"):
        return file_store.resolve(val_str), manifest, None

    if val_str.startswith("file://"):
        parsed = urllib.parse.urlparse(val_str)
        file_path = urllib.parse.unquote(parsed.path)
        if len(file_path) > 2 and file_path[0] == "/" and file_path[2] == ":":
            file_path = file_path[1:]
        return Path(file_path).resolve(), manifest, None

    path_obj = Path(val_str).resolve()
    if path_obj.is_file():
        return path_obj, manifest, None

    return None, None, Issue(
        code="E-FILE-NOT-FOUND",
        severity=Severity.ERROR,
        engine=Engine.DOCX,
        message=f"Cannot resolve template input or template_id '{template_ref_or_id}'.",
    )


def docx_render_template(
    template_ref_or_id: Union[str, FileRef, Dict[str, Any], Path],
    context_data: Dict[str, Any],
    layout_policy: Optional[Union[Dict[str, Any], LayoutPolicy]] = None,
    manifest: Optional[Union[Dict[str, Any], TemplateManifest]] = None,
    output_path: Optional[Union[str, Path]] = None,
    file_store: Optional[FileStore] = None,
    template_registry: Optional[TemplateRegistry] = None,
) -> ResultEnvelope:
    """
    Renders a DOCX template with context data using Jinja2 SandboxedEnvironment.
    Applies OOXML guards and manifest constraints.
    """
    fs = file_store or FileStore()
    t_reg = template_registry or get_default_template_registry()
    diag = Diagnostics(engine=Engine.DOCX)

    resolved_path, reg_manifest, err = _resolve_template_input(template_ref_or_id, fs, t_reg)
    if err is not None:
        diag.add_issue(err)
        return ResultEnvelope(success=False, diagnostics=diag)

    if resolved_path is None or not resolved_path.is_file():
        diag.add_issue(Issue(
            code="E-FILE-NOT-FOUND",
            severity=Severity.ERROR,
            engine=Engine.DOCX,
            message=f"Template file does not exist: {resolved_path}",
        ))
        return ResultEnvelope(success=False, diagnostics=diag)

    # Use explicit manifest if passed, else registered manifest
    active_manifest: Optional[TemplateManifest] = reg_manifest
    if manifest is not None:
        if isinstance(manifest, dict):
            active_manifest = TemplateManifest.model_validate(manifest)
        else:
            active_manifest = manifest

    # Convert layout_policy if dict
    active_policy: Optional[LayoutPolicy] = None
    if layout_policy is not None:
        if isinstance(layout_policy, dict):
            active_policy = LayoutPolicy.model_validate(layout_policy)
        else:
            active_policy = layout_policy

    render_res = jinja_renderer.render(
        template_input=resolved_path,
        context_data=context_data,
        manifest=active_manifest,
        layout_policy=active_policy,
        normalize_first=True,
    )

    for iss in render_res.issues:
        diag.add_issue(iss)

    if any(i.severity == Severity.ERROR for i in render_res.issues):
        return ResultEnvelope(success=False, diagnostics=diag)

    # Store output file
    out_fileref: Optional[FileRef] = None
    if output_path is not None:
        dest = Path(output_path).resolve()
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(render_res.docx_bytes)
        out_fileref = fs.store_file(dest, mime=_DOCX_MIME, engine="docx")
    else:
        out_fileref = fs.store_bytes(
            data=render_res.docx_bytes,
            mime=_DOCX_MIME,
            engine="docx",
            filename_hint=f"rendered_{resolved_path.name}",
        )

    stats = Stats(
        elements_processed=render_res.stats.get("tables_guarded", 0),
        extra=render_res.stats,
    )

    return ResultEnvelope(
        success=True,
        file_ref=out_fileref,
        diagnostics=diag,
        guarantees_applied=render_res.guarantees_applied,
        stats=stats,
    )


def docx_build_document(
    source_type: str = "template",
    template_id: Optional[str] = None,
    template_ref: Optional[Union[str, FileRef, Dict[str, Any], Path]] = None,
    docspec: Optional[Dict[str, Any]] = None,
    context_data: Optional[Dict[str, Any]] = None,
    layout_policy: Optional[Union[Dict[str, Any], LayoutPolicy]] = None,
    output_path: Optional[Union[str, Path]] = None,
    file_store: Optional[FileStore] = None,
    template_registry: Optional[TemplateRegistry] = None,
) -> ResultEnvelope:
    """Unified MCP builder entry point: dispatches Path A (Template) or Path B (DocSpec)."""
    if source_type == "template":
        target_ref = template_id or template_ref
        if not target_ref:
            diag = Diagnostics(engine=Engine.DOCX)
            diag.add_issue(Issue(
                code="E-DOCX-SPEC-INVALID",
                severity=Severity.ERROR,
                engine=Engine.DOCX,
                message="Template-based build requires either 'template_id' or 'template_ref'.",
            ))
            return ResultEnvelope(success=False, diagnostics=diag)

        return docx_render_template(
            template_ref_or_id=target_ref,
            context_data=context_data or {},
            layout_policy=layout_policy,
            output_path=output_path,
            file_store=file_store,
            template_registry=template_registry,
        )

    # Path B will be hooked up in Sub-step 1.1.4
    diag = Diagnostics(engine=Engine.DOCX)
    diag.add_issue(Issue(
        code="E-DOCX-PATH-B-PENDING",
        severity=Severity.ERROR,
        engine=Engine.DOCX,
        message=f"Source type '{source_type}' will be active in Sub-step 1.1.4.",
    ))
    return ResultEnvelope(success=False, diagnostics=diag)


def register_build_ops(registry: Any) -> None:
    """Registers docx.render_template and docx.build_document tools into Registry."""

    @registry.register(
        name="docx.render_template",
        description="Dựng tài liệu Word từ template Jinja2 qua SandboxedEnvironment và áp dụng rào chắn OOXML.",
    )
    def _render_tool(
        template_ref_or_id: Any,
        context_data: Dict[str, Any],
        layout_policy: Optional[Dict[str, Any]] = None,
        manifest: Optional[Dict[str, Any]] = None,
        output_path: Optional[str] = None,
    ) -> ResultEnvelope:
        return docx_render_template(
            template_ref_or_id=template_ref_or_id,
            context_data=context_data,
            layout_policy=layout_policy,
            manifest=manifest,
            output_path=output_path,
            file_store=registry.file_store,
        )

    @registry.register(
        name="docx.build_document",
        description="Bộ điều phối dựng tài liệu Word thống nhất: Path A (Template Jinja) và Path B (DocSpec JSON).",
    )
    def _build_tool(
        source_type: str = "template",
        template_id: Optional[str] = None,
        template_ref: Optional[Any] = None,
        docspec: Optional[Dict[str, Any]] = None,
        context_data: Optional[Dict[str, Any]] = None,
        layout_policy: Optional[Dict[str, Any]] = None,
        output_path: Optional[str] = None,
    ) -> ResultEnvelope:
        return docx_build_document(
            source_type=source_type,
            template_id=template_id,
            template_ref=template_ref,
            docspec=docspec,
            context_data=context_data,
            layout_policy=layout_policy,
            output_path=output_path,
            file_store=registry.file_store,
        )

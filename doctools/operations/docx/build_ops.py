"""
doctools.operations.docx.build_ops
MCP Tool Operations for document building:
- docx.render_template: Path A Template rendering with Jinja2 sandboxing and OOXML guards.
- docx.build_document: Unified dispatcher for Path A (Template) and Path B (DocSpec).
"""

from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, Optional, Union
import urllib.parse

import docx as docx_module

from doctools.contract import (
    Diagnostics,
    Engine,
    FileRef,
    Issue,
    ResultEnvelope,
    Severity,
    Stats,
)
from doctools.contract.docx.docspec import DocSpec
from doctools.contract.docx.manifest import LayoutPolicy, TemplateManifest
from doctools.core.docx.build import docspec_builder, jinja_renderer
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
        rec = template_registry.get(template_ref_or_id)
        if rec is not None:
            return file_store.resolve(rec.file_ref), rec.manifest, None

    input_val = template_ref_or_id
    if isinstance(input_val, dict) and "uri" in input_val:
        input_val = FileRef(**input_val)

    if isinstance(input_val, FileRef):
        return file_store.resolve(input_val), manifest, None

    if isinstance(input_val, Path):
        return input_val.resolve(), manifest, None

    val_str = str(input_val).strip()
    if val_str.startswith("resource://"):
        return file_store.resolve(val_str), manifest, None

    if val_str.startswith("file://"):
        parsed = urllib.parse.urlparse(val_str)
        p = urllib.parse.unquote(parsed.path)
        if len(p) > 2 and p[0] == "/" and p[2] == ":":
            p = p[1:]
        return Path(p).resolve(), manifest, None

    path_obj = Path(val_str).resolve()
    if path_obj.is_file():
        return path_obj, manifest, None

    return None, None, Issue(
        code="E-FILE-NOT-FOUND",
        severity=Severity.ERROR,
        engine=Engine.DOCX,
        message=f"Cannot resolve template input or template_id '{template_ref_or_id}'.",
    )


def _store_docx_output(
    fs: FileStore,
    data: bytes,
    out_path: Optional[Union[str, Path]],
    hint: str,
) -> FileRef:
    """Helper to store rendered DOCX bytes to filesystem destination or FileStore."""
    if out_path is not None:
        dest = Path(out_path).resolve()
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        return fs.store_file(dest, mime=_DOCX_MIME, engine="docx")
    return fs.store_bytes(data=data, mime=_DOCX_MIME, engine="docx", filename_hint=hint)


def docx_render_template(
    template_ref_or_id: Union[str, FileRef, Dict[str, Any], Path],
    context_data: Dict[str, Any],
    layout_policy: Optional[Union[Dict[str, Any], LayoutPolicy]] = None,
    manifest: Optional[Union[Dict[str, Any], TemplateManifest]] = None,
    output_path: Optional[Union[str, Path]] = None,
    file_store: Optional[FileStore] = None,
    template_registry: Optional[TemplateRegistry] = None,
) -> ResultEnvelope:
    """Renders a DOCX template with context data using Jinja2 SandboxedEnvironment."""
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

    active_manifest = reg_manifest
    if manifest is not None:
        active_manifest = TemplateManifest.model_validate(manifest) if isinstance(manifest, dict) else manifest

    active_policy = None
    if layout_policy is not None:
        active_policy = LayoutPolicy.model_validate(layout_policy) if isinstance(layout_policy, dict) else layout_policy

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

    out_fileref = _store_docx_output(fs, render_res.docx_bytes, output_path, f"rendered_{resolved_path.name}")
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
    docspec: Optional[Union[Dict[str, Any], DocSpec]] = None,
    context_data: Optional[Dict[str, Any]] = None,
    layout_policy: Optional[Union[Dict[str, Any], LayoutPolicy]] = None,
    output_path: Optional[Union[str, Path]] = None,
    file_store: Optional[FileStore] = None,
    template_registry: Optional[TemplateRegistry] = None,
) -> ResultEnvelope:
    """Unified MCP builder entry point: dispatches Path A (Template) or Path B (DocSpec)."""
    fs = file_store or FileStore()
    t_reg = template_registry or get_default_template_registry()
    diag = Diagnostics(engine=Engine.DOCX)

    if source_type == "template":
        target_ref = template_id or template_ref
        if not target_ref:
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
            file_store=fs,
            template_registry=t_reg,
        )

    if source_type == "docspec":
        if not docspec:
            diag.add_issue(Issue(
                code="E-DOCX-DOCSPEC-MISSING",
                severity=Severity.ERROR,
                engine=Engine.DOCX,
                message="DocSpec-based build requires non-empty 'docspec' payload.",
            ))
            return ResultEnvelope(success=False, diagnostics=diag)

        # Resolve optional base template
        base_doc: Optional[Any] = None
        base_ref = docspec.get("base_template") if isinstance(docspec, dict) else getattr(docspec, "base_template", None)
        if base_ref:
            b_path, _, _ = _resolve_template_input(base_ref, fs, t_reg)
            if b_path and b_path.is_file():
                base_doc = docx_module.Document(b_path)

        active_policy = None
        if layout_policy is not None:
            active_policy = LayoutPolicy.model_validate(layout_policy) if isinstance(layout_policy, dict) else layout_policy

        build_res = docspec_builder.build(
            docspec_input=docspec,
            base_doc=base_doc,
            layout_policy=active_policy,
        )

        for iss in build_res.issues:
            diag.add_issue(iss)

        if any(i.severity == Severity.ERROR for i in build_res.issues):
            return ResultEnvelope(success=False, diagnostics=diag)

        out_fileref = _store_docx_output(fs, build_res.docx_bytes, output_path, "built_docspec.docx")
        stats = Stats(
            elements_processed=build_res.stats.get("tables", 0) + build_res.stats.get("paragraphs", 0),
            extra=build_res.stats,
        )
        return ResultEnvelope(
            success=True,
            file_ref=out_fileref,
            diagnostics=diag,
            guarantees_applied=build_res.guarantees_applied,
            stats=stats,
        )

    diag.add_issue(Issue(
        code="E-DOCX-SOURCE-TYPE-UNKNOWN",
        severity=Severity.ERROR,
        engine=Engine.DOCX,
        message=f"Unsupported source_type '{source_type}'. Choose 'template' or 'docspec'.",
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

"""
doctools.core.docx.build.jinja_renderer
Path A: Template-driven document builder using docxtpl, Jinja2 SandboxedEnvironment,
and OOXML layout guards (cantSplit, tblHeader, vAlign, keepNext).
"""

from __future__ import annotations
import hashlib
import io
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import docx
from docxtpl import DocxTemplate
from jinja2.sandbox import SandboxedEnvironment

from doctools.contract import Engine, Issue, Severity, Location
from doctools.contract.docx.manifest import LayoutPolicy, TemplateManifest
from doctools.core.docx.schema import schema_helper
from doctools.core.docx.template.jinja_normalizer import jinja_normalizer


class RenderResult:
    """Holds rendered DOCX bytes, diagnostics, guarantees, and stats."""

    def __init__(
        self,
        docx_bytes: bytes,
        issues: List[Issue],
        guarantees_applied: List[str],
        stats: Dict[str, Any],
    ) -> None:
        self.docx_bytes = docx_bytes
        self.issues = issues
        self.guarantees_applied = guarantees_applied
        self.stats = stats


class JinjaRenderer:
    """
    Renders Word templates deterministically within a Jinja2 SandboxedEnvironment.
    Enforces manifest immutability checks and injects native OOXML guards.
    """

    def __init__(self) -> None:
        self.schema_helper = schema_helper

    def render(
        self,
        template_input: Union[Path, bytes, str],
        context_data: Dict[str, Any],
        manifest: Optional[TemplateManifest] = None,
        layout_policy: Optional[LayoutPolicy] = None,
        normalize_first: bool = True,
    ) -> RenderResult:
        """
        Executes Path A template rendering:
        1. Validates immutability and character constraints against manifest.
        2. Normalizes template to heal run splitting if enabled.
        3. Renders context into template using Jinja2 SandboxedEnvironment.
        4. Applies preventive OOXML guards per layout_policy.
        """
        issues: List[Issue] = []
        guarantees: List[str] = []

        # 1. Resolve raw template bytes
        raw_bytes: bytes
        if isinstance(template_input, bytes):
            raw_bytes = template_input
        else:
            raw_bytes = Path(template_input).resolve().read_bytes()

        # 2. Immutability & Constraint Validation (FR-13)
        if manifest:
            self._validate_manifest_constraints(manifest, context_data, issues)
            if any(i.severity == Severity.ERROR for i in issues):
                return RenderResult(b"", issues, guarantees, {})

        # 3. Normalize template runs (FR-02)
        if normalize_first:
            norm_res = jinja_normalizer.normalize(raw_bytes)
            raw_bytes = norm_res.normalized_bytes
            guarantees.append("jinja_runs_normalized")

        # 4. Render with docxtpl in SandboxedEnvironment (SEC-01)
        doc = DocxTemplate(io.BytesIO(raw_bytes))
        sandbox_env = SandboxedEnvironment(autoescape=True)

        try:
            doc.render(context_data, jinja_env=sandbox_env)
            guarantees.append("sandboxed_jinja_render")
        except Exception as exc:
            issues.append(
                Issue(
                    code="E-DOCX-RENDER-FAILED",
                    severity=Severity.ERROR,
                    engine=Engine.DOCX,
                    message=f"Template rendering failed in sandbox: {exc}",
                )
            )
            return RenderResult(b"", issues, guarantees, {})

        # 5. Apply Preventive OOXML Guards (FR-07)
        policy = layout_policy
        if policy is None and manifest is not None:
            policy = manifest.layout_policy_default
        if policy is None:
            policy = LayoutPolicy()

        effective_doc = doc.docx
        guard_stats = self._apply_ooxml_guards(effective_doc, policy, guarantees)

        # 6. Save rendered bytes
        out_buf = io.BytesIO()
        effective_doc.save(out_buf)
        rendered_bytes = out_buf.getvalue()

        stats = {
            "tables_guarded": guard_stats["tables"],
            "rows_guarded": guard_stats["rows"],
            "headings_guarded": guard_stats["headings"],
            "output_size_bytes": len(rendered_bytes),
        }

        return RenderResult(
            docx_bytes=rendered_bytes,
            issues=issues,
            guarantees_applied=guarantees,
            stats=stats,
        )

    def _validate_manifest_constraints(
        self,
        manifest: TemplateManifest,
        context_data: Dict[str, Any],
        issues: List[Issue],
    ) -> None:
        """Validates variable immutability and max_chars length restrictions."""
        for var_name, var_def in manifest.variables.items():
            if var_name not in context_data:
                continue

            val = context_data[var_name]

            # Character limit check
            if var_def.max_chars is not None:
                char_len = len(str(val))
                if char_len > var_def.max_chars:
                    issues.append(
                        Issue(
                            code="W-DOCX-MAX-CHARS-EXCEEDED",
                            severity=Severity.WARNING,
                            engine=Engine.DOCX,
                            message=(
                                f"Variable '{var_name}' length ({char_len}) exceeds "
                                f"manifest max_chars ({var_def.max_chars})."
                            ),
                            location=Location(element=f"variable:{var_name}"),
                            evidence={"variable": var_name, "length": char_len, "limit": var_def.max_chars},
                            fixable_by="ai",
                        )
                    )

            # Immutability validation (FR-13)
            if var_def.immutable:
                # Value must be provided and non-empty
                if val is None or (isinstance(val, str) and not val.strip()):
                    issues.append(
                        Issue(
                            code="E-DOCX-IMMUTABLE-VIOLATION",
                            severity=Severity.ERROR,
                            engine=Engine.DOCX,
                            message=f"Immutable variable '{var_name}' cannot be empty or omitted.",
                            location=Location(element=f"variable:{var_name}"),
                            evidence={"variable": var_name},
                            fixable_by="human",
                        )
                    )

    def _apply_ooxml_guards(
        self,
        doc: Any,
        policy: LayoutPolicy,
        guarantees: List[str],
    ) -> Dict[str, int]:
        """Applies cantSplit, tblHeader, vAlign, and keepNext OOXML guards."""
        stats = {"tables": 0, "rows": 0, "headings": 0}

        should_apply = policy.apply_guards == "apply"

        # Apply Table Guards
        for tbl in doc.tables:
            stats["tables"] += 1
            for row_idx, row in enumerate(tbl.rows):
                stats["rows"] += 1
                if should_apply:
                    self.schema_helper.set_tr_cant_split(row, True)
                    if row_idx == 0:
                        self.schema_helper.set_tr_header(row, True)

                for cell in row.cells:
                    if should_apply:
                        self.schema_helper.set_tc_valign(cell, "center")
                    self.schema_helper.ensure_cell_last_p(cell)

        if should_apply and stats["tables"] > 0:
            guarantees.extend(["guards:cantSplit", "guards:tblHeader", "guards:vAlign"])
        guarantees.append("guards:last_paragraph_rule")

        # Apply Heading Guards (keepNext)
        for p in doc.paragraphs:
            if p.style and p.style.name.startswith("Heading"):
                stats["headings"] += 1
                if should_apply:
                    self.schema_helper.set_p_keep_next(p, True)

        if should_apply and stats["headings"] > 0:
            guarantees.append("guards:keepNext")

        return stats


# Global singleton instance
jinja_renderer = JinjaRenderer()

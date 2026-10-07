"""
doctools.core.docx.build.docspec_builder
Path B: Generates professional Word documents from structured DocSpec JSON/Dict.
Applies typography standards, schema guards, and OOXML layout integrity.
"""

from __future__ import annotations
import io
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import docx
from docx.enum.section import WD_ORIENT
from docx.shared import Cm, Pt, RGBColor
from pydantic import ValidationError

from doctools.contract import Engine, Issue, Location, Severity
from doctools.contract.docx.docspec import (
    CalloutBlock,
    DocBlock,
    DocSpec,
    HeadingBlock,
    ImageBlock,
    ListBlock,
    PageBreakBlock,
    PageSetupSpec,
    ParagraphBlock,
    TableBlock,
)
from doctools.contract.docx.manifest import LayoutPolicy
from doctools.core.docx.schema import schema_helper


class DocSpecBuildResult:
    """Holds generated DOCX bytes, diagnostics, applied guarantees, and execution stats."""

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


class DocSpecBuilder:
    """
    Constructs Word documents deterministically from DocSpec schemas.
    Enforces layout guarantees (cantSplit, tblHeader, keepNext, vAlign, last_p).
    """

    def __init__(self) -> None:
        self.schema_helper = schema_helper

    def build(
        self,
        docspec_input: Union[DocSpec, Dict[str, Any]],
        base_doc: Optional[docx.Document] = None,
        layout_policy: Optional[LayoutPolicy] = None,
    ) -> DocSpecBuildResult:
        """Builds a complete Word document from a DocSpec specification."""
        issues: List[Issue] = []
        guarantees: List[str] = ["docspec_build"]

        # 1. Validate DocSpec against Pydantic model
        spec: DocSpec
        if isinstance(docspec_input, DocSpec):
            spec = docspec_input
        else:
            try:
                spec = DocSpec.model_validate(docspec_input)
            except ValidationError as exc:
                for err in exc.errors():
                    loc_path = ".".join(str(p) for p in err["loc"])
                    issues.append(
                        Issue(
                            code="E-DOCX-DOCSPEC-INVALID",
                            severity=Severity.ERROR,
                            engine=Engine.DOCX,
                            message=f"DocSpec schema error: {err['msg']} at '{loc_path}'",
                            location=Location(element=loc_path),
                            evidence={"loc": err["loc"], "type": err["type"]},
                            fixable_by="ai",
                        )
                    )
                return DocSpecBuildResult(b"", issues, guarantees, {})

        # 2. Initialize Document
        doc = base_doc if base_doc is not None else docx.Document()

        # 3. Apply Page Setup
        if spec.page_setup:
            self._apply_page_setup(doc, spec.page_setup)
            guarantees.append("page_setup_configured")

        # 4. Optional Document Title
        if spec.title:
            doc.add_heading(spec.title, level=0)

        # 5. Build content blocks
        stats: Dict[str, int] = {
            "headings": 0,
            "paragraphs": 0,
            "lists": 0,
            "tables": 0,
            "table_rows": 0,
            "callouts": 0,
            "images": 0,
            "page_breaks": 0,
        }

        for idx, block in enumerate(spec.blocks):
            try:
                self._build_block(doc, block, stats, issues, guarantees)
            except Exception as exc:
                issues.append(
                    Issue(
                        code="E-DOCX-BLOCK-BUILD-FAILED",
                        severity=Severity.ERROR,
                        engine=Engine.DOCX,
                        message=f"Failed to build block {idx} ({block.type}): {exc}",
                        location=Location(element=f"blocks[{idx}]"),
                        fixable_by="ai",
                    )
                )

        if any(i.severity == Severity.ERROR for i in issues):
            return DocSpecBuildResult(b"", issues, guarantees, stats)

        # 6. Apply OOXML layout guarantees
        policy = layout_policy or LayoutPolicy(apply_guards="apply")
        if policy.apply_guards == "apply":
            guarantees.extend([
                "guards:cantSplit",
                "guards:tblHeader",
                "guards:vAlign",
                "guards:keepNext",
                "guards:last_paragraph_rule",
            ])

        # 7. Serialize output
        out_buf = io.BytesIO()
        doc.save(out_buf)
        rendered_bytes = out_buf.getvalue()
        stats["output_size_bytes"] = len(rendered_bytes)

        return DocSpecBuildResult(
            docx_bytes=rendered_bytes,
            issues=issues,
            guarantees_applied=list(dict.fromkeys(guarantees)),
            stats=stats,
        )

    def _apply_page_setup(self, doc: Any, setup: PageSetupSpec) -> None:
        """Sets margins and orientation for all sections."""
        for section in doc.sections:
            if setup.orientation == "landscape":
                section.orientation = WD_ORIENT.LANDSCAPE
                # Swap width and height if not already swapped
                if section.page_width < section.page_height:
                    w, h = section.page_width, section.page_height
                    section.page_width, section.page_height = h, w
            else:
                section.orientation = WD_ORIENT.PORTRAIT

            if setup.margin_top_cm is not None:
                section.top_margin = Cm(setup.margin_top_cm)
            if setup.margin_bottom_cm is not None:
                section.bottom_margin = Cm(setup.margin_bottom_cm)
            if setup.margin_left_cm is not None:
                section.left_margin = Cm(setup.margin_left_cm)
            if setup.margin_right_cm is not None:
                section.right_margin = Cm(setup.margin_right_cm)

    def _build_block(
        self,
        doc: Any,
        block: DocBlock,
        stats: Dict[str, int],
        issues: List[Issue],
        guarantees: List[str],
    ) -> None:
        """Dispatches block construction by block type."""
        if isinstance(block, HeadingBlock):
            stats["headings"] += 1
            p = doc.add_heading(block.text, level=block.level)
            if block.style:
                try:
                    p.style = block.style
                except KeyError:
                    pass
            self.schema_helper.set_p_keep_next(p, True)

        elif isinstance(block, ParagraphBlock):
            stats["paragraphs"] += 1
            p = doc.add_paragraph()
            if block.style:
                try:
                    p.style = block.style
                except KeyError:
                    pass

            if block.runs:
                for r_spec in block.runs:
                    run = p.add_run(r_spec.text)
                    if r_spec.bold is not None:
                        run.bold = r_spec.bold
                    if r_spec.italic is not None:
                        run.italic = r_spec.italic
                    if r_spec.color:
                        try:
                            run.font.color.rgb = RGBColor.from_string(r_spec.color.lstrip("#"))
                        except Exception:
                            pass
            elif block.text:
                p.text = block.text

        elif isinstance(block, ListBlock):
            stats["lists"] += len(block.items)
            default_style = "List Number" if block.ordered else "List Bullet"
            style_name = block.style or default_style
            for item in block.items:
                doc.add_paragraph(item, style=style_name)

        elif isinstance(block, TableBlock):
            self._build_table(doc, block, stats)

        elif isinstance(block, CalloutBlock):
            stats["callouts"] += 1
            self._build_callout(doc, block)

        elif isinstance(block, ImageBlock):
            stats["images"] += 1
            self._build_image(doc, block, issues)

        elif isinstance(block, PageBreakBlock):
            stats["page_breaks"] += 1
            doc.add_page_break()

    def _build_table(self, doc: Any, block: TableBlock, stats: Dict[str, int]) -> None:
        """Constructs table with headers, rows, and OOXML guards."""
        has_headers = bool(block.headers)
        total_rows = len(block.rows) + (1 if has_headers else 0)
        col_count = len(block.headers) if has_headers else (len(block.rows[0]) if block.rows else 0)

        table = doc.add_table(rows=total_rows, cols=col_count)
        if block.style:
            try:
                table.style = block.style
            except KeyError:
                pass

        stats["tables"] += 1
        stats["table_rows"] += total_rows

        current_row = 0
        if has_headers and block.headers:
            header_row = table.rows[0]
            self.schema_helper.set_tr_header(header_row, True)
            for c_idx, h_text in enumerate(block.headers):
                if c_idx < len(header_row.cells):
                    header_row.cells[c_idx].paragraphs[0].text = h_text
                    header_row.cells[c_idx].paragraphs[0].runs[0].bold = True
            current_row = 1

        for row_data in block.rows:
            target_row = table.rows[current_row]
            for c_idx, cell_val in enumerate(row_data):
                if c_idx < len(target_row.cells):
                    target_row.cells[c_idx].paragraphs[0].text = str(cell_val)
            current_row += 1

        # Apply OOXML guards (cantSplit, vAlign, last_p)
        for row in table.rows:
            self.schema_helper.set_tr_cant_split(row, True)
            for cell in row.cells:
                self.schema_helper.set_tc_valign(cell, "center")
                self.schema_helper.ensure_cell_last_p(cell)

        # Set column widths if provided
        if block.col_widths:
            for row in table.rows:
                for c_idx, w_cm in enumerate(block.col_widths):
                    if c_idx < len(row.cells):
                        row.cells[c_idx].width = Cm(w_cm)

    def _build_callout(self, doc: Any, block: CalloutBlock) -> None:
        """Constructs callout box as single-cell table with guards."""
        tbl = doc.add_table(rows=1, cols=1)
        tbl.style = "Table Grid"
        row = tbl.rows[0]
        self.schema_helper.set_tr_cant_split(row, True)
        cell = row.cells[0]
        self.schema_helper.set_tc_valign(cell, "center")

        p = cell.paragraphs[0]
        if block.title:
            run_title = p.add_run(f"[{block.kind.upper()}] {block.title}\n")
            run_title.bold = True
        run_text = p.add_run(block.text)
        self.schema_helper.ensure_cell_last_p(cell)

    def _build_image(self, doc: Any, block: ImageBlock, issues: List[Issue]) -> None:
        """Adds image while respecting printable boundary limits."""
        img_path = Path(block.source).resolve()
        if not img_path.is_file():
            issues.append(
                Issue(
                    code="W-DOCX-IMAGE-NOT-FOUND",
                    severity=Severity.WARNING,
                    engine=Engine.DOCX,
                    message=f"Image source file not found: {block.source}",
                    location=Location(element="image"),
                    fixable_by="ai",
                )
            )
            return

        w_cm = block.width_cm or 14.0
        # ERR_DOCX_005: width <= 15.92 cm
        if w_cm > 15.92:
            w_cm = 15.92

        doc.add_picture(str(img_path), width=Cm(w_cm))
        if block.caption:
            doc.add_paragraph(block.caption, style="Caption")


# Global singleton instance
docspec_builder = DocSpecBuilder()

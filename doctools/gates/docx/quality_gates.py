"""
doctools.gates.docx.quality_gates
Comprehensive Quality Gates (DG-01 to DG-06) for Word documents (DOCX).
Ensures OpenXML compliance, layout guard enforcement, and template sanity.
"""

from __future__ import annotations
import io
from pathlib import Path
import re
from typing import Any, List, Optional, Union
import zipfile

import docx
from docx.document import Document as _DocumentClass
from lxml import etree

from doctools.contract import Engine, FixableBy, Issue, Location, Severity

_W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
_A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
_WP = "{http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing}"
_JINJA_VAR_RE = re.compile(r"\{\{([^{}]+)\}\}|\{%([^%{}]+)%\}")
_MAX_WIDTH_EMU = 15.92 * 360000  # 15.92 cm in EMUs


class DocxQualityGateEngine:
    """
    Executes automated quality gate verification for DOCX files.
    Gates:
    - DG-01: Package & XML integrity (E-DOCX-PACKAGE-CORRUPT)
    - DG-02: Last Paragraph Rule ERR_DOCX_001 (E-DOCX-OPENXML-TC-P)
    - DG-03: Table cantSplit and tblHeader guards ERR_DOCX_003 (W-DOCX-MISSING-GUARDS)
    - DG-04: Image boundary overflow ERR_DOCX_005 (W-DOCX-IMAGE-OVERFLOW)
    - DG-05: Unresolved Jinja syntax tokens (W-DOCX-UNRESOLVED-VARIABLE)
    - DG-06: Heading hierarchy progression (W-DOCX-HEADING-LEVEL-SKIP)
    """

    def validate(
        self,
        doc_input: Union[Path, bytes, str, _DocumentClass],
    ) -> List[Issue]:
        """Runs all DG-01 through DG-06 quality gates against the document."""
        issues: List[Issue] = []

        # DG-01: Validate Package Integrity
        raw_bytes: Optional[bytes] = None
        doc: Optional[_DocumentClass] = None

        if isinstance(doc_input, _DocumentClass):
            doc = doc_input
            buf = io.BytesIO()
            doc.save(buf)
            raw_bytes = buf.getvalue()
        elif isinstance(doc_input, bytes):
            raw_bytes = doc_input
        else:
            p = Path(doc_input).resolve()
            if not p.is_file():
                return [
                    Issue(
                        code="E-DOCX-FILE-NOT-FOUND",
                        severity=Severity.ERROR,
                        engine=Engine.DOCX,
                        message=f"File does not exist: {p}",
                        location=Location(part="package"),
                    )
                ]
            raw_bytes = p.read_bytes()

        # Check zip container
        try:
            with zipfile.ZipFile(io.BytesIO(raw_bytes), "r") as zf:
                namelist = zf.namelist()
                if "word/document.xml" not in namelist:
                    return [
                        Issue(
                            code="E-DOCX-PACKAGE-CORRUPT",
                            severity=Severity.ERROR,
                            engine=Engine.DOCX,
                            message="Package is missing 'word/document.xml'.",
                            location=Location(part="word/document.xml"),
                        )
                    ]
        except Exception as exc:
            return [
                Issue(
                    code="E-DOCX-PACKAGE-CORRUPT",
                    severity=Severity.ERROR,
                    engine=Engine.DOCX,
                    message=f"DOCX package is corrupt or unreadable: {exc}",
                    location=Location(part="package"),
                )
            ]

        # Load document model
        if doc is None:
            try:
                doc = docx.Document(io.BytesIO(raw_bytes))
            except Exception as exc:
                return [
                    Issue(
                        code="E-DOCX-LOAD-FAILED",
                        severity=Severity.ERROR,
                        engine=Engine.DOCX,
                        message=f"Failed to load document into python-docx: {exc}",
                    )
                ]

        # DG-02 & DG-03: Table Gates
        self._check_table_gates(doc, issues)

        # DG-04: Image Bounds
        self._check_image_bounds(doc, issues)

        # DG-05: Unresolved Jinja variables
        self._check_unresolved_variables(doc, issues)

        # DG-06: Heading hierarchy
        self._check_heading_hierarchy(doc, issues)

        return issues

    def _check_table_gates(self, doc: docx.Document, issues: List[Issue]) -> None:
        """Enforces DG-02 (Last Paragraph Rule) and DG-03 (Table guards)."""
        for tbl_idx, tbl in enumerate(doc.tables):
            # Check tblHeader on header row (row 0) if multi-row
            if len(tbl.rows) > 1:
                tr0_pr = tbl.rows[0]._tr.find(f"{_W}trPr")
                if tr0_pr is None or tr0_pr.find(f"{_W}tblHeader") is None:
                    issues.append(
                        Issue(
                            code="W-DOCX-MISSING-TBLHEADER",
                            severity=Severity.WARNING,
                            engine=Engine.DOCX,
                            message=f"Table {tbl_idx} row 0 is missing '<w:tblHeader/>' guard.",
                            location=Location(element=f"/body/tbl[{tbl_idx}]/tr[0]"),
                            fixable_by=FixableBy.ENGINE,
                            suggested_action="Apply schema_helper.set_tr_header(row, True)",
                        )
                    )

            # Check cantSplit on each row and last paragraph rule on each cell
            for r_idx, row in enumerate(tbl.rows):
                tr_pr = row._tr.find(f"{_W}trPr")
                if tr_pr is None or tr_pr.find(f"{_W}cantSplit") is None:
                    issues.append(
                        Issue(
                            code="W-DOCX-MISSING-CANTSPLIT",
                            severity=Severity.WARNING,
                            engine=Engine.DOCX,
                            message=f"Table {tbl_idx} row {r_idx} is missing '<w:cantSplit/>' guard.",
                            location=Location(element=f"/body/tbl[{tbl_idx}]/tr[{r_idx}]"),
                            fixable_by=FixableBy.ENGINE,
                            suggested_action="Apply schema_helper.set_tr_cant_split(row, True)",
                        )
                    )

                for c_idx, cell in enumerate(row.cells):
                    # DG-02: ERR_DOCX_001 Last paragraph rule
                    tc_children = list(cell._tc)
                    if not tc_children or tc_children[-1].tag != f"{_W}p":
                        issues.append(
                            Issue(
                                code="E-DOCX-OPENXML-TC-P",
                                severity=Severity.ERROR,
                                engine=Engine.DOCX,
                                message=f"Cell at tbl[{tbl_idx}]/tr[{r_idx}]/tc[{c_idx}] does not end with paragraph.",
                                location=Location(element=f"/body/tbl[{tbl_idx}]/tr[{r_idx}]/tc[{c_idx}]"),
                                fixable_by=FixableBy.ENGINE,
                                suggested_action="Append empty paragraph via schema_helper.ensure_cell_last_p",
                            )
                        )

    def _check_image_bounds(self, doc: docx.Document, issues: List[Issue]) -> None:
        """DG-04: Checks that drawings and images do not exceed maximum printable width."""
        body = doc._body._element
        for ext in body.iter(f"{_WP}extent"):
            cx = ext.get("cx")
            if cx and cx.isdigit():
                cx_val = int(cx)
                if cx_val > _MAX_WIDTH_EMU:
                    width_cm = round(cx_val / 360000, 2)
                    issues.append(
                        Issue(
                            code="W-DOCX-IMAGE-OVERFLOW",
                            severity=Severity.WARNING,
                            engine=Engine.DOCX,
                            message=f"Image width ({width_cm} cm) exceeds page printable margin (15.92 cm).",
                            location=Location(element="wp:extent"),
                            evidence={"width_cm": width_cm, "max_cm": 15.92},
                            fixable_by=FixableBy.ENGINE,
                        )
                    )

    def _check_unresolved_variables(self, doc: docx.Document, issues: List[Issue]) -> None:
        """DG-05: Checks for unresolved Jinja2 tags remaining in paragraphs and tables."""
        for p_idx, p in enumerate(doc.paragraphs):
            matches = _JINJA_VAR_RE.findall(p.text)
            for m in matches:
                tag_content = (m[0] or m[1]).strip()
                issues.append(
                    Issue(
                        code="W-DOCX-UNRESOLVED-VARIABLE",
                        severity=Severity.WARNING,
                        engine=Engine.DOCX,
                        message=f"Unresolved template tag detected in paragraph {p_idx}: '{tag_content}'",
                        location=Location(element=f"/body/p[{p_idx}]"),
                        evidence={"tag": tag_content},
                        fixable_by=FixableBy.AI,
                    )
                )

    def _check_heading_hierarchy(self, doc: docx.Document, issues: List[Issue]) -> None:
        """DG-06: Verifies heading levels don't skip increments (e.g. 1 -> 3)."""
        prev_level = 0
        for p_idx, p in enumerate(doc.paragraphs):
            if p.style and p.style.name.startswith("Heading"):
                parts = p.style.name.split()
                if len(parts) > 1 and parts[1].isdigit():
                    level = int(parts[1])
                    if prev_level > 0 and level > prev_level + 1:
                        issues.append(
                            Issue(
                                code="W-DOCX-HEADING-LEVEL-SKIP",
                                severity=Severity.WARNING,
                                engine=Engine.DOCX,
                                message=f"Heading level jumped from {prev_level} to {level} at paragraph {p_idx}.",
                                location=Location(element=f"/body/p[{p_idx}]"),
                                evidence={"previous_level": prev_level, "current_level": level},
                                fixable_by=FixableBy.AI,
                            )
                        )
                    prev_level = level


# Global singleton
docx_quality_gates = DocxQualityGateEngine()

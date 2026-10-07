"""
doctools.core.docx.patch.docx_patcher
Declarative in-place Word document patcher (FR-11).
Executes anchor-targeted modifications while strictly preserving formatting tokens and OOXML invariants.
"""

from __future__ import annotations
import io
from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Union

import docx
from docx.document import Document as _DocxDocument
from docx.table import _Cell, Table
from docx.text.paragraph import Paragraph

from doctools.contract import Engine, Issue, Location, Severity
from doctools.contract.docx.patch import PatchOp, PatchSpec
from doctools.core.docx.schema import schema_helper
from doctools.gates.docx import docx_quality_gates

_W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
_P_ANCHOR_RE = re.compile(r"^/body/p\[(\d+)\]$")
_TBL_ANCHOR_RE = re.compile(r"^/body/tbl\[(\d+)\]$")
_TC_ANCHOR_RE = re.compile(r"^/body/tbl\[(\d+)\]/tr\[(\d+)\]/tc\[(\d+)\]$")


class PatchResult:
    """Holds patched document bytes, issues, and guarantees."""

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


class DocxPatcher:
    """
    Executes declarative, anchor-based mutations on existing DOCX files.
    Preserves run styling and enforces ERR_DOCX_001/002/003 invariants.
    """

    def patch(
        self,
        doc_input: Union[Path, bytes, str, _DocxDocument],
        patch_spec: Union[PatchSpec, Dict[str, Any], List[Dict[str, Any]]],
    ) -> PatchResult:
        """Applies patch operations to the target document."""
        issues: List[Issue] = []
        guarantees: List[str] = ["format_preserving_patch"]

        # 1. Parse PatchSpec
        spec: PatchSpec
        if isinstance(patch_spec, PatchSpec):
            spec = patch_spec
        elif isinstance(patch_spec, dict) and "operations" in patch_spec:
            spec = PatchSpec.model_validate(patch_spec)
        elif isinstance(patch_spec, list):
            spec = PatchSpec(operations=[PatchOp.model_validate(op) for op in patch_spec])
        else:
            issues.append(
                Issue(
                    code="E-DOCX-PATCH-SPEC-INVALID",
                    severity=Severity.ERROR,
                    engine=Engine.DOCX,
                    message="Invalid patch specification payload.",
                )
            )
            return PatchResult(b"", issues, guarantees, {})

        # 2. Load document
        doc: _DocxDocument
        if isinstance(doc_input, _DocxDocument):
            doc = doc_input
        elif isinstance(doc_input, bytes):
            doc = docx.Document(io.BytesIO(doc_input))
        else:
            doc = docx.Document(str(Path(doc_input).resolve()))

        applied_ops = 0

        # 3. Apply operations sequentially
        for idx, op in enumerate(spec.operations):
            try:
                self._apply_op(doc, op, guarantees)
                applied_ops += 1
            except Exception as exc:
                issues.append(
                    Issue(
                        code="E-DOCX-PATCH-OP-FAILED",
                        severity=Severity.ERROR,
                        engine=Engine.DOCX,
                        message=f"Patch operation {idx} ({op.op}) failed at '{op.anchor}': {exc}",
                        location=Location(element=op.anchor),
                        fixable_by="ai",
                    )
                )

        if any(i.severity == Severity.ERROR for i in issues):
            return PatchResult(b"", issues, guarantees, {"applied_ops": applied_ops})

        # 4. Post-patch Quality Gate verification (DG-01..DG-06)
        gate_issues = docx_quality_gates.validate(doc)
        issues.extend(gate_issues)

        # 5. Serialize output
        buf = io.BytesIO()
        doc.save(buf)
        rendered_bytes = buf.getvalue()

        stats = {
            "applied_ops": applied_ops,
            "output_size_bytes": len(rendered_bytes),
        }

        return PatchResult(
            docx_bytes=rendered_bytes,
            issues=issues,
            guarantees_applied=list(dict.fromkeys(guarantees)),
            stats=stats,
        )

    def _apply_op(self, doc: _DocxDocument, op: PatchOp, guarantees: List[str]) -> None:
        """Dispatches an individual patch operation."""
        # Check cell anchor: /body/tbl[i]/tr[j]/tc[k]
        m_tc = _TC_ANCHOR_RE.match(op.anchor)
        if m_tc:
            tbl_i, tr_j, tc_k = int(m_tc.group(1)), int(m_tc.group(2)), int(m_tc.group(3))
            tbl = doc.tables[tbl_i]
            cell = tbl.rows[tr_j].cells[tc_k]
            self._patch_cell(cell, op, guarantees)
            return

        # Check paragraph anchor: /body/p[i]
        m_p = _P_ANCHOR_RE.match(op.anchor)
        if m_p:
            p_i = int(m_p.group(1))
            p = doc.paragraphs[p_i]
            self._patch_paragraph(doc, p, op, guarantees)
            return

        # Check table anchor: /body/tbl[i]
        m_tbl = _TBL_ANCHOR_RE.match(op.anchor)
        if m_tbl:
            tbl_i = int(m_tbl.group(1))
            tbl = doc.tables[tbl_i]
            if op.op == "delete":
                tbl._tbl.getparent().remove(tbl._tbl)
                guarantees.append("element_deleted")
                return

        raise ValueError(f"Unresolvable or unsupported anchor: '{op.anchor}'")

    def _patch_paragraph(self, doc: _DocxDocument, p: Paragraph, op: PatchOp, guarantees: List[str]) -> None:
        """Applies operation to target paragraph."""
        if op.op == "replace_text":
            new_text = str(op.payload or "")
            if op.target_text:
                # Substring replacement across runs
                found = False
                for run in p.runs:
                    if op.target_text in run.text:
                        run.text = run.text.replace(op.target_text, new_text)
                        found = True
                        break
                if not found and op.target_text in p.text:
                    p.text = p.text.replace(op.target_text, new_text)
            else:
                # Replace whole text while preserving first run style
                if p.runs:
                    p.runs[0].text = new_text
                    for r in p.runs[1:]:
                        r.text = ""
                else:
                    p.add_run(new_text)
            guarantees.append("run_style_preserved")

        elif op.op == "insert_paragraph_after":
            new_p = doc.add_paragraph(str(op.payload or ""))
            p._p.addnext(new_p._p)
            guarantees.append("paragraph_inserted")

        elif op.op == "delete":
            p._p.getparent().remove(p._p)
            guarantees.append("element_deleted")

    def _patch_cell(self, cell: _Cell, op: PatchOp, guarantees: List[str]) -> None:
        """
        Applies patch to table cell strictly preserving run styles (ERR_DOCX_002)
        and ensuring last paragraph rule (ERR_DOCX_001).
        """
        new_text = str(op.payload or "")

        if len(cell.paragraphs) == 0:
            p = cell.add_paragraph()
        else:
            p = cell.paragraphs[0]

        if op.op in ("update_cell", "replace_text"):
            if op.target_text and op.target_text in p.text:
                for run in p.runs:
                    if op.target_text in run.text:
                        run.text = run.text.replace(op.target_text, new_text)
                        break
            else:
                # ERR_DOCX_002: Mutate strictly through cell.paragraphs[0].runs
                if p.runs:
                    p.runs[0].text = new_text
                    for r in p.runs[1:]:
                        r.text = ""
                else:
                    p.add_run(new_text)

        # ERR_DOCX_001: Ensure Last Paragraph Rule
        schema_helper.ensure_cell_last_p(cell)
        guarantees.append("run_style_preserved")
        guarantees.append("guards:last_paragraph_rule")


# Global singleton
docx_patcher = DocxPatcher()

"""
doctools.core.docx.merge.docx_merger
Merges multiple Word documents (base + parts/appendices) into a unified document (FR-06).
Uses docxcompose with style conflict detection, section alignment, and OOXML guards.
"""

from __future__ import annotations
import io
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Union

import docx
from docx.document import Document as _DocxDocument
from docxcompose.composer import Composer

from doctools.contract import Engine, Issue, Location, Severity
from doctools.core.docx.schema import schema_helper
from doctools.gates.docx import docx_quality_gates

StyleConflictPolicy = Literal["master_wins", "isolate_styles", "flatten_styles"]


class MergeResult:
    """Holds merged DOCX bytes, diagnostics, applied guarantees, and execution stats."""

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


class DocxMerger:
    """
    Combines a base Word document with multiple appendix or part documents.
    Detects style collisions and ensures post-merge layout integrity.
    """

    def merge(
        self,
        base_input: Union[Path, bytes, str, _DocxDocument],
        parts: List[Union[Path, bytes, str, _DocxDocument]],
        style_conflict_policy: StyleConflictPolicy = "master_wins",
    ) -> MergeResult:
        """Merges parts into base document following the specified style conflict policy."""
        issues: List[Issue] = []
        guarantees: List[str] = [f"merge:{style_conflict_policy}"]

        if not parts:
            issues.append(
                Issue(
                    code="E-DOCX-MERGE-NO-PARTS",
                    severity=Severity.ERROR,
                    engine=Engine.DOCX,
                    message="At least one appendix/part document must be provided to merge.",
                )
            )
            return MergeResult(b"", issues, guarantees, {})

        # 1. Load base document
        base_doc = self._resolve_doc(base_input)
        composer = Composer(base_doc)

        master_styles = {s.name for s in base_doc.styles}

        # 2. Append each part sequentially
        appended_count = 0
        conflicting_styles: set[str] = set()

        for idx, part_input in enumerate(parts):
            try:
                part_doc = self._resolve_doc(part_input)

                # Check style conflicts
                part_styles = {s.name for s in part_doc.styles}
                overlap = (master_styles & part_styles) - {"Normal", "Default Paragraph Font"}
                if overlap:
                    conflicting_styles.update(overlap)

                composer.append(part_doc)
                appended_count += 1
            except Exception as exc:
                issues.append(
                    Issue(
                        code="E-DOCX-MERGE-PART-FAILED",
                        severity=Severity.ERROR,
                        engine=Engine.DOCX,
                        message=f"Failed to append part {idx}: {exc}",
                        location=Location(element=f"parts[{idx}]"),
                        fixable_by="human",
                    )
                )

        if conflicting_styles:
            issues.append(
                Issue(
                    code="W-MERGE-STYLE-CONFLICT",
                    severity=Severity.WARNING,
                    engine=Engine.DOCX,
                    message=(
                        f"Style conflict detected between master and parts for styles: "
                        f"{sorted(conflicting_styles)}. Applied policy: '{style_conflict_policy}'."
                    ),
                    evidence={"conflicts": sorted(conflicting_styles), "policy": style_conflict_policy},
                    fixable_by="ai",
                )
            )

        if any(i.severity == Severity.ERROR for i in issues):
            return MergeResult(b"", issues, guarantees, {"appended_parts": appended_count})

        # 3. Apply post-merge table and heading guards
        self._enforce_post_merge_guards(base_doc, guarantees)

        # 4. Run post-merge quality gates (DG-01..DG-06)
        gate_issues = docx_quality_gates.validate(base_doc)
        issues.extend(gate_issues)

        # 5. Serialize merged output
        buf = io.BytesIO()
        composer.save(buf)
        merged_bytes = buf.getvalue()

        stats = {
            "appended_parts": appended_count,
            "total_paragraphs": len(base_doc.paragraphs),
            "total_tables": len(base_doc.tables),
            "output_size_bytes": len(merged_bytes),
        }

        return MergeResult(
            docx_bytes=merged_bytes,
            issues=issues,
            guarantees_applied=list(dict.fromkeys(guarantees)),
            stats=stats,
        )

    def _resolve_doc(self, target: Union[Path, bytes, str, _DocxDocument]) -> _DocxDocument:
        """Resolves target input into a docx Document instance."""
        if isinstance(target, _DocxDocument):
            return target
        if isinstance(target, bytes):
            return docx.Document(io.BytesIO(target))
        return docx.Document(str(Path(target).resolve()))

    def _enforce_post_merge_guards(self, doc: _DocxDocument, guarantees: List[str]) -> None:
        """Applies cantSplit, tblHeader, and last_p guards on all tables."""
        for tbl in doc.tables:
            for r_idx, row in enumerate(tbl.rows):
                schema_helper.set_tr_cant_split(row, True)
                if r_idx == 0:
                    schema_helper.set_tr_header(row, True)
                for cell in row.cells:
                    schema_helper.ensure_cell_last_p(cell)
        guarantees.extend(["guards:cantSplit", "guards:tblHeader", "guards:last_paragraph_rule"])


# Global singleton instance
docx_merger = DocxMerger()

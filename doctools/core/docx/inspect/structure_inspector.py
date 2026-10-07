"""
doctools.core.docx.inspect.structure_inspector
Inspects DOCX structure, producing a deterministic hierarchical tree with stable anchors.
Used by AI agents to navigate document layout and plan modifications.
"""

from __future__ import annotations
import io
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import docx
from docx.document import Document as _DocumentClass
from docx.table import Table
from docx.text.paragraph import Paragraph

_W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


class StructureInspector:
    """
    Parses a Word document into an anchor-indexed structural AST.
    Anchors use XPath-like addresses: /body/p[0], /body/tbl[0]/tr[1]/tc[2].
    """

    def inspect(self, doc_input: Union[Path, bytes, str, _DocumentClass]) -> Dict[str, Any]:
        """Inspects document and returns hierarchical structural tree with anchors."""
        doc: _DocumentClass
        if isinstance(doc_input, _DocumentClass):
            doc = doc_input
        elif isinstance(doc_input, bytes):
            doc = docx.Document(io.BytesIO(doc_input))
        else:
            doc = docx.Document(str(Path(doc_input).resolve()))

        nodes: List[Dict[str, Any]] = []
        headings: List[Dict[str, Any]] = []
        table_count = 0
        p_count = 0
        total_words = 0

        # Traverse body children sequentially
        body = doc._body._element
        p_idx = 0
        tbl_idx = 0

        for child in body.iterchildren():
            tag = child.tag
            if tag == f"{_W}p":
                p_obj = Paragraph(child, doc)
                p_info = self._inspect_paragraph(p_obj, p_idx)
                nodes.append(p_info)
                if p_info.get("heading_level") is not None:
                    headings.append({
                        "anchor": p_info["anchor"],
                        "level": p_info["heading_level"],
                        "text": p_info["text"],
                    })
                total_words += len(p_info["text"].split())
                p_count += 1
                p_idx += 1

            elif tag == f"{_W}tbl":
                tbl_obj = Table(child, doc)
                tbl_info = self._inspect_table(tbl_obj, tbl_idx)
                nodes.append(tbl_info)
                table_count += 1
                tbl_idx += 1

        stats = {
            "paragraph_count": p_count,
            "table_count": table_count,
            "heading_count": len(headings),
            "word_count": total_words,
            "section_count": len(doc.sections),
        }

        return {
            "root": "/body",
            "stats": stats,
            "headings_outline": headings,
            "children": nodes,
        }

    def _inspect_paragraph(self, p: Paragraph, idx: int) -> Dict[str, Any]:
        """Inspects paragraph properties, style, runs, and heading level."""
        text = p.text
        style_name = p.style.name if p.style else "Normal"
        heading_level: Optional[int] = None

        if style_name.startswith("Heading"):
            parts = style_name.split()
            if len(parts) > 1 and parts[1].isdigit():
                heading_level = int(parts[1])
        elif style_name == "Title":
            heading_level = 0

        # Check for page break inside paragraph
        has_page_break = False
        for run in p.runs:
            if "lastRenderedPageBreak" in run._r.xml or "<w:br" in run._r.xml:
                has_page_break = True
                break

        return {
            "type": "paragraph",
            "id": f"p_{idx}",
            "anchor": f"/body/p[{idx}]",
            "style": style_name,
            "heading_level": heading_level,
            "text": text,
            "run_count": len(p.runs),
            "has_page_break": has_page_break,
        }

    def _inspect_table(self, tbl: Table, idx: int) -> Dict[str, Any]:
        """Inspects table dimensions, header row, and cell anchors."""
        row_count = len(tbl.rows)
        col_count = len(tbl.columns) if row_count > 0 else 0
        style_name = tbl.style.name if tbl.style else "Table Grid"

        # Check for tblHeader on row 0
        has_tbl_header = False
        if row_count > 0:
            trPr = tbl.rows[0]._tr.find(f"{_W}trPr")
            if trPr is not None and trPr.find(f"{_W}tblHeader") is not None:
                has_tbl_header = True

        rows_data: List[Dict[str, Any]] = []
        for r_idx, row in enumerate(tbl.rows):
            # Check cantSplit
            trPr = row._tr.find(f"{_W}trPr")
            has_cant_split = trPr is not None and trPr.find(f"{_W}cantSplit") is not None

            cells_data: List[Dict[str, Any]] = []
            for c_idx, cell in enumerate(row.cells):
                cells_data.append({
                    "anchor": f"/body/tbl[{idx}]/tr[{r_idx}]/tc[{c_idx}]",
                    "text": cell.text,
                    "paragraph_count": len(cell.paragraphs),
                })

            rows_data.append({
                "anchor": f"/body/tbl[{idx}]/tr[{r_idx}]",
                "row_index": r_idx,
                "has_cant_split": has_cant_split,
                "cells": cells_data,
            })

        return {
            "type": "table",
            "id": f"tbl_{idx}",
            "anchor": f"/body/tbl[{idx}]",
            "style": style_name,
            "row_count": row_count,
            "col_count": col_count,
            "has_header_guard": has_tbl_header,
            "rows": rows_data,
        }


# Global singleton
structure_inspector = StructureInspector()

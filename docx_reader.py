"""
docx_reader.py — DOCX → JSON Snapshot for AI editing.

Reads a .docx file and exports a structured JSON representation containing:
  - sections: page size, margins, header/footer text
  - body elements: paragraphs (with runs, style, alignment, spacing),
                   tables (cells with nested paragraphs, colspan/rowspan),
                   images (id, alt_text, dimensions)
  - hyperlinks (embedded in paragraph runs)

The JSON snapshot is designed to be AI-readable and round-trippable
via docx_writer.py.
"""

from __future__ import annotations

import json
import os
from typing import Any

from docx import Document
from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _emu_to_cm(emu: int | None) -> float | None:
    """Convert EMU (English Metric Units) to centimetres."""
    if emu is None:
        return None
    return round(emu / 914400 * 2.54, 3)


def _pt_to_num(pt_value) -> float | None:
    """Convert Pt object or raw half-points to float pt value."""
    if pt_value is None:
        return None
    try:
        return round(float(pt_value.pt), 2)
    except AttributeError:
        try:
            return round(float(pt_value) / 2, 2)
        except Exception:
            return None


def _rgb_to_hex(color: RGBColor | None) -> str | None:
    if color is None:
        return None
    try:
        return f"#{color.rgb}"
    except Exception:
        return None


def _align_to_str(alignment) -> str:
    if alignment is None:
        return "LEFT"
    mapping = {
        WD_ALIGN_PARAGRAPH.LEFT:       "LEFT",
        WD_ALIGN_PARAGRAPH.CENTER:     "CENTER",
        WD_ALIGN_PARAGRAPH.RIGHT:      "RIGHT",
        WD_ALIGN_PARAGRAPH.JUSTIFY:    "JUSTIFY",
        WD_ALIGN_PARAGRAPH.DISTRIBUTE: "DISTRIBUTE",
    }
    return mapping.get(alignment, str(alignment))


# ---------------------------------------------------------------------------
# Hyperlink extraction
# ---------------------------------------------------------------------------

def _get_paragraph_hyperlinks(paragraph) -> list[dict]:
    """Extract all hyperlinks in a paragraph as {url, display_text}."""
    links = []
    part = paragraph.part
    for child in paragraph._element:
        if child.tag == qn("w:hyperlink"):
            try:
                rId = child.get(qn("r:id"))
                url = part.rels[rId].target_ref if rId else None
            except (KeyError, AttributeError):
                url = None
            link_text = "".join(
                t.text for t in child.iter(qn("w:t")) if t.text
            )
            links.append({"url": url, "display_text": link_text})
    return links


# ---------------------------------------------------------------------------
# Run serialisation
# ---------------------------------------------------------------------------

def _serialise_run(run, run_index: int) -> dict[str, Any]:
    font = run.font
    color = None
    try:
        color = _rgb_to_hex(font.color.rgb) if font.color.type is not None else None
    except Exception:
        pass

    return {
        "run_index": run_index,
        "text": run.text,
        "bold": run.bold,
        "italic": run.italic,
        "underline": run.underline,
        "strike": font.strike,
        "font_name": font.name,
        "font_size": _pt_to_num(font.size) if font.size else None,
        "font_color": color,
        "highlight_color": str(font.highlight_color) if font.highlight_color else None,
    }


# ---------------------------------------------------------------------------
# Paragraph serialisation
# ---------------------------------------------------------------------------

def _serialise_paragraph(paragraph, element_index: int) -> dict[str, Any]:
    fmt = paragraph.paragraph_format

    # Safely extract list indent level
    indent_level = 0
    try:
        pPr = paragraph._p.pPr
        if pPr is not None and pPr.numPr is not None and pPr.numPr.ilvl is not None:
            indent_level = pPr.numPr.ilvl.val
    except Exception:
        pass

    # line_spacing may be Pt or a float multiplier
    line_spacing = None
    try:
        ls = fmt.line_spacing
        if isinstance(ls, Pt):
            line_spacing = _pt_to_num(ls)
        elif ls is not None:
            line_spacing = float(ls)
    except Exception:
        pass

    runs = [_serialise_run(run, i) for i, run in enumerate(paragraph.runs)]
    hyperlinks = _get_paragraph_hyperlinks(paragraph)

    return {
        "element_index": element_index,
        "type": "paragraph",
        "style_name": paragraph.style.name if paragraph.style else "Normal",
        "text": paragraph.text,
        "alignment": _align_to_str(paragraph.alignment),
        "indent_level": indent_level,
        "space_before_pt": _pt_to_num(fmt.space_before),
        "space_after_pt": _pt_to_num(fmt.space_after),
        "line_spacing": line_spacing,
        "left_indent_pt": _pt_to_num(fmt.left_indent),
        "first_line_indent_pt": _pt_to_num(fmt.first_line_indent),
        "runs": runs,
        "hyperlinks": hyperlinks,
    }


# ---------------------------------------------------------------------------
# Table serialisation
# ---------------------------------------------------------------------------

def _get_cell_shading(tc_element) -> str | None:
    """Return hex fill color from <w:tcPr>/<w:shd> or None."""
    tcPr = tc_element.find(qn("w:tcPr"))
    if tcPr is None:
        return None
    shd = tcPr.find(qn("w:shd"))
    if shd is not None:
        fill = shd.get(qn("w:fill"))
        if fill and fill.lower() not in ("auto", "none", "transparent"):
            return f"#{fill.upper()}"
    return None


def _get_cell_span(tc_element) -> tuple[int, int]:
    """Return (colspan, rowspan) from raw <w:tc> XML."""
    tcPr = tc_element.find(qn("w:tcPr"))
    if tcPr is None:
        return 1, 1

    grid_span = tcPr.find(qn("w:gridSpan"))
    colspan = int(grid_span.get(qn("w:val"), 1)) if grid_span is not None else 1

    v_merge = tcPr.find(qn("w:vMerge"))
    if v_merge is not None:
        val = v_merge.get(qn("w:val"), "continue")
        rowspan = 1 if val == "restart" else 0  # 0 = continuation cell
    else:
        rowspan = 1

    return colspan, rowspan


def _serialise_table(table, element_index: int) -> dict[str, Any]:
    rows_data = []
    for r_idx, row in enumerate(table.rows):
        cells_data = []
        # Check if row has tblHeader flag
        trPr = row._tr.find(qn("w:trPr"))
        is_tbl_header = (trPr is not None and trPr.find(qn("w:tblHeader")) is not None) or (r_idx == 0)

        for c_idx, cell in enumerate(row.cells):
            tc = cell._tc
            colspan, rowspan = _get_cell_span(tc)
            shading = _get_cell_shading(tc)
            paras = []
            for p_idx, p in enumerate(cell.paragraphs):
                pd = _serialise_paragraph(p, p_idx)
                pd.pop("element_index", None)
                paras.append(pd)

            cells_data.append({
                "row": r_idx,
                "col": c_idx,
                "colspan": colspan,
                "rowspan": rowspan,
                "fill_color": shading,
                "is_header": is_tbl_header,
                "text": cell.text,
                "paragraphs": paras,
            })
        rows_data.append(cells_data)

    return {
        "element_index": element_index,
        "type": "table",
        "rows": len(table.rows),
        "cols": len(table.columns),
        "cells": rows_data,
    }


# ---------------------------------------------------------------------------
# Image serialisation
# ---------------------------------------------------------------------------

_NS_A  = "http://schemas.openxmlformats.org/drawingml/2006/main"
_NS_WP = "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"


def _serialise_image(drawing_element, element_index: int) -> dict[str, Any] | None:
    """Extract image metadata from a <w:drawing> element."""
    inline = drawing_element.find(f"{{{_NS_WP}}}inline")
    anchor = drawing_element.find(f"{{{_NS_WP}}}anchor")
    container = inline if inline is not None else anchor
    if container is None:
        return None

    extent = container.find(f"{{{_NS_WP}}}extent")
    width_emu  = int(extent.get("cx", 0)) if extent is not None else 0
    height_emu = int(extent.get("cy", 0)) if extent is not None else 0

    doc_pr = container.find(f"{{{_NS_WP}}}docPr")
    alt_text   = doc_pr.get("descr", "") if doc_pr is not None else ""
    image_name = doc_pr.get("name",  "") if doc_pr is not None else ""

    blip = drawing_element.find(f".//{{{_NS_A}}}blip")
    r_id = None
    if blip is not None:
        r_id = blip.get(
            "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed"
        )

    return {
        "element_index": element_index,
        "type": "image",
        "image_id": r_id,
        "image_name": image_name,
        "alt_text": alt_text,
        "width_cm":  _emu_to_cm(width_emu),
        "height_cm": _emu_to_cm(height_emu),
    }


# ---------------------------------------------------------------------------
# Section serialisation
# ---------------------------------------------------------------------------

def _serialise_sections(doc: Document) -> list[dict[str, Any]]:
    sections_data = []
    for s_idx, section in enumerate(doc.sections):
        header_text = ""
        footer_text = ""
        try:
            if section.header and section.header.paragraphs:
                header_text = "\n".join(p.text for p in section.header.paragraphs)
        except Exception:
            pass
        try:
            if section.footer and section.footer.paragraphs:
                footer_text = "\n".join(p.text for p in section.footer.paragraphs)
        except Exception:
            pass

        sections_data.append({
            "section_index":    s_idx,
            "page_width_cm":    _emu_to_cm(section.page_width),
            "page_height_cm":   _emu_to_cm(section.page_height),
            "margin_top_cm":    _emu_to_cm(section.top_margin),
            "margin_bottom_cm": _emu_to_cm(section.bottom_margin),
            "margin_left_cm":   _emu_to_cm(section.left_margin),
            "margin_right_cm":  _emu_to_cm(section.right_margin),
            "header_text": header_text.strip(),
            "footer_text": footer_text.strip(),
        })
    return sections_data


# ---------------------------------------------------------------------------
# Body traversal
# ---------------------------------------------------------------------------

def _iter_body_elements(doc: Document) -> list[dict[str, Any]]:
    """
    Traverse doc.element.body children in document order,
    returning serialised paragraphs, tables, and images.
    """
    from docx.text.paragraph import Paragraph
    from docx.table import Table

    body = doc.element.body
    element_index = 0
    result = []

    for child in body:
        tag = child.tag

        if tag == qn("w:p"):
            para = Paragraph(child, doc)
            drawings = child.findall(f".//{qn('w:drawing')}")
            if drawings:
                for drawing in drawings:
                    img = _serialise_image(drawing, element_index)
                    if img:
                        result.append(img)
                        element_index += 1
            else:
                result.append(_serialise_paragraph(para, element_index))
                element_index += 1

        elif tag == qn("w:tbl"):
            tbl = Table(child, doc)
            result.append(_serialise_table(tbl, element_index))
            element_index += 1

    return result


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def read_docx(docx_path: str) -> dict[str, Any]:
    """
    Read a DOCX file and return a structured JSON-serialisable snapshot.

    Args:
        docx_path: Absolute path to the .docx file.

    Returns:
        dict with keys: source_file, snapshot_version, sections, body
    """
    if not os.path.isfile(docx_path):
        raise FileNotFoundError(f"File not found: {docx_path}")

    doc = Document(docx_path)

    return {
        "source_file": os.path.abspath(docx_path),
        "snapshot_version": "1.0",
        "sections": _serialise_sections(doc),
        "body": _iter_body_elements(doc),
    }


def read_docx_to_json(docx_path: str, output_path: str | None = None) -> str:
    """
    Read DOCX and write JSON snapshot to output_path (or return as string).

    Args:
        docx_path:   Path to source .docx file.
        output_path: Optional path to write JSON output.
                     If None, returns JSON string to stdout.

    Returns:
        output_path if written to file, else the JSON string.
    """
    snapshot = read_docx(docx_path)
    json_str = json.dumps(snapshot, ensure_ascii=False, indent=2)

    if output_path:
        out_dir = os.path.dirname(os.path.abspath(output_path))
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(json_str)
        return output_path

    return json_str

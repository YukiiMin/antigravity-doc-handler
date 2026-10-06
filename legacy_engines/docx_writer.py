"""
docx_writer.py — JSON Snapshot → DOCX for AI editing round-trip.

Takes a JSON snapshot (produced by docx_reader.py) and writes it back
into a DOCX file. Supports an optional template DOCX to use as a style
anchor — style names from the snapshot are looked up in the template's
style gallery, ensuring pixel-accurate formatting without hardcoding.

Supported element types in the JSON body:
  - paragraph: style_name, alignment, runs (bold/italic/underline/font)
  - table: rows × cols with nested paragraph cells
  - image: NOT re-embedded (images are read-only placeholders in this version)
"""

from __future__ import annotations

import copy
import json
import os
import shutil
from typing import Any

from docx import Document
from docx.shared import Pt, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

# Maximum sane Pt value Word accepts (≈ 1584pt = 22 inches)
_MAX_PT = 1584.0


def _safe_pt(value: float | None) -> Pt | None:
    """Return Pt(value) only if value is within Word's legal range."""
    if value is None:
        return None
    if abs(value) > _MAX_PT:
        return None
    return Pt(value)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_ALIGN_MAP: dict[str, WD_ALIGN_PARAGRAPH] = {
    "LEFT":       WD_ALIGN_PARAGRAPH.LEFT,
    "CENTER":     WD_ALIGN_PARAGRAPH.CENTER,
    "RIGHT":      WD_ALIGN_PARAGRAPH.RIGHT,
    "JUSTIFY":    WD_ALIGN_PARAGRAPH.JUSTIFY,
    "DISTRIBUTE": WD_ALIGN_PARAGRAPH.DISTRIBUTE,
}


def _hex_to_rgb(hex_color: str | None) -> RGBColor | None:
    if not hex_color:
        return None
    h = hex_color.lstrip("#")
    if len(h) != 6:
        return None
    try:
        return RGBColor(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
    except ValueError:
        return None


def _apply_run_format(run, run_data: dict[str, Any]) -> None:
    """Apply formatting attributes from a run dict onto a python-docx Run."""
    if run_data.get("bold") is not None:
        run.bold = run_data["bold"]
    if run_data.get("italic") is not None:
        run.italic = run_data["italic"]
    if run_data.get("underline") is not None:
        run.underline = run_data["underline"]
    if run_data.get("strike"):
        run.font.strike = True
    if run_data.get("font_name"):
        run.font.name = run_data["font_name"]
    size_pt = _safe_pt(run_data.get("font_size"))
    if size_pt is not None:
        run.font.size = size_pt
    color = _hex_to_rgb(run_data.get("font_color"))
    if color:
        run.font.color.rgb = color


def _set_keep_next(para) -> None:
    """Ensure paragraph has <w:keepNext/> so Word does not break page after it."""
    pPr = para._element.get_or_add_pPr()
    if pPr.find(qn("w:keepNext")) is None:
        pPr.append(OxmlElement("w:keepNext"))


def _apply_paragraph_format(para, para_data: dict[str, Any]) -> None:
    """Apply paragraph-level spacing/indent/alignment from a para dict."""
    fmt = para.paragraph_format
    alignment = _ALIGN_MAP.get(para_data.get("alignment", "LEFT"), WD_ALIGN_PARAGRAPH.LEFT)
    para.alignment = alignment

    sb = _safe_pt(para_data.get("space_before_pt"))
    if sb is not None:
        fmt.space_before = sb
    sa = _safe_pt(para_data.get("space_after_pt"))
    if sa is not None:
        fmt.space_after = sa
    li = _safe_pt(para_data.get("left_indent_pt"))
    if li is not None:
        fmt.left_indent = li
    fli = _safe_pt(para_data.get("first_line_indent_pt"))
    if fli is not None:
        fmt.first_line_indent = fli
    if para_data.get("line_spacing") is not None:
        ls = para_data["line_spacing"]
        # If > 4, treat as Pt value; otherwise treat as line multiplier
        if ls > 4:
            safe = _safe_pt(ls)
            if safe is not None:
                fmt.line_spacing = safe
        else:
            fmt.line_spacing = ls

    if para_data.get("keep_next"):
        _set_keep_next(para)


# ---------------------------------------------------------------------------
# Style resolution
# ---------------------------------------------------------------------------

def _resolve_style(doc: Document, style_name: str):
    """
    Return the style object from doc matching style_name.
    Falls back to 'Normal' if not found.
    """
    try:
        return doc.styles[style_name]
    except KeyError:
        # Try case-insensitive
        lower = style_name.lower()
        for s in doc.styles:
            if s.name.lower() == lower:
                return s
        return doc.styles["Normal"]


# ---------------------------------------------------------------------------
# Element writers
# ---------------------------------------------------------------------------

def _write_paragraph(doc: Document, para_data: dict[str, Any]) -> None:
    style_name = para_data.get("style_name", "Normal")
    style = _resolve_style(doc, style_name)
    para = doc.add_paragraph(style=style)

    _apply_paragraph_format(para, para_data)

    for run_data in para_data.get("runs", []):
        run = para.add_run(run_data.get("text", ""))
        _apply_run_format(run, run_data)

    # If runs are empty but there's a top-level text, add it as plain run
    if not para_data.get("runs") and para_data.get("text"):
        para.add_run(para_data["text"])


def _set_cell_shading(tc_elem, hex_color: str | None) -> None:
    """Apply XML shading <w:shd> to a table cell."""
    if not hex_color:
        return
    h = hex_color.lstrip("#").upper()
    if len(h) != 6:
        return
    tcPr = tc_elem.get_or_add_tcPr()
    # Remove existing shd if any
    for existing in tcPr.findall(qn("w:shd")):
        tcPr.remove(existing)
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), h)
    tcPr.append(shd)


def _set_cell_margins(tc_elem, top: int = 120, bottom: int = 120, left: int = 150, right: int = 150) -> None:
    """Set cell padding/margins via <w:tcMar> in dxa (1 pt = 20 dxa)."""
    tcPr = tc_elem.get_or_add_tcPr()
    for existing in tcPr.findall(qn("w:tcMar")):
        tcPr.remove(existing)
    tcMar = OxmlElement("w:tcMar")
    for side, val in (("top", top), ("bottom", bottom), ("left", left), ("right", right)):
        node = OxmlElement(f"w:{side}")
        node.set(qn("w:w"), str(val))
        node.set(qn("w:type"), "dxa")
        tcMar.append(node)
    tcPr.append(tcMar)


def _set_cell_borders(tc_elem, color_hex: str = "CBD5E1", sz: str = "4") -> None:
    """Set subtle cell borders via <w:tcBorders>."""
    tcPr = tc_elem.get_or_add_tcPr()
    for existing in tcPr.findall(qn("w:tcBorders")):
        tcPr.remove(existing)
    tcBorders = OxmlElement("w:tcBorders")
    for side in ("top", "left", "bottom", "right"):
        b_elem = OxmlElement(f"w:{side}")
        b_elem.set(qn("w:val"), "single")
        b_elem.set(qn("w:sz"), sz)
        b_elem.set(qn("w:space"), "0")
        b_elem.set(qn("w:color"), color_hex.lstrip("#"))
        tcBorders.append(b_elem)
    tcPr.append(tcBorders)


def _set_row_flags(tr_elem, is_header: bool = False, cant_split: bool = True) -> None:
    """Set <w:tblHeader> and <w:cantSplit> in <w:trPr>."""
    trPr = tr_elem.get_or_add_trPr()
    if cant_split and trPr.find(qn("w:cantSplit")) is None:
        trPr.append(OxmlElement("w:cantSplit"))
    if is_header and trPr.find(qn("w:tblHeader")) is None:
        trPr.append(OxmlElement("w:tblHeader"))


def _write_table(doc: Document, table_data: dict[str, Any]) -> None:
    rows = table_data.get("rows", 1)
    cols = table_data.get("cols", 1)
    table = doc.add_table(rows=rows, cols=cols)
    table.style = "Table Grid"

    cells_flat = table_data.get("cells", [])
    for r_idx, row_cells in enumerate(cells_flat):
        if r_idx >= rows:
            break
        row = table.rows[r_idx]
        is_header_row = (r_idx == 0) or any(c.get("is_header") for c in row_cells)
        _set_row_flags(row._tr, is_header=is_header_row, cant_split=True)

        for cell_data in row_cells:
            c_idx = cell_data.get("col", 0)
            if c_idx >= cols:
                continue

            cell = table.cell(r_idx, c_idx)
            tc = cell._tc

            # Apply cell margins & borders
            _set_cell_margins(tc, top=120, bottom=120, left=150, right=150)
            _set_cell_borders(tc, color_hex="CBD5E1", sz="4")

            # Apply fill / shading
            fill_color = cell_data.get("fill_color")
            if not fill_color and is_header_row:
                fill_color = "#1F4E78"  # Default navy header fill
            if fill_color:
                _set_cell_shading(tc, fill_color)

            # Clear default empty paragraph using XML
            for p_elem in tc.findall(qn("w:p")):
                tc.remove(p_elem)

            for para_data in cell_data.get("paragraphs", []):
                style_name = para_data.get("style_name", "Normal")
                style = _resolve_style(doc, style_name)
                para = cell.add_paragraph(style=style)
                _apply_paragraph_format(para, para_data)

                for run_data in para_data.get("runs", []):
                    run = para.add_run(run_data.get("text", ""))
                    _apply_run_format(run, run_data)
                    # For header rows with dark background, ensure white text if not explicitly set
                    if is_header_row and fill_color in ("#1F4E78", "#2C3E50", "#000080", "#333399"):
                        if not run_data.get("font_color"):
                            run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
                            run.bold = True

                if not para_data.get("runs") and para_data.get("text"):
                    run = para.add_run(para_data["text"])
                    if is_header_row and fill_color in ("#1F4E78", "#2C3E50", "#000080", "#333399"):
                        run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
                        run.bold = True


def _write_image_placeholder(doc: Document, img_data: dict[str, Any]) -> None:
    """Add a text placeholder for images (not re-embedded in v1)."""
    alt = img_data.get("alt_text") or img_data.get("image_name") or img_data.get("image_id") or "IMAGE"
    w = img_data.get("width_cm", "?")
    h = img_data.get("height_cm", "?")
    para = doc.add_paragraph(style=_resolve_style(doc, "Normal"))
    run = para.add_run(f"[IMAGE: {alt} | {w}cm × {h}cm]")
    run.italic = True
    run.font.color.rgb = RGBColor(0x99, 0x99, 0x99)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def write_docx(
    snapshot: dict[str, Any],
    output_path: str,
    template_path: str | None = None,
) -> str:
    """
    Write a DOCX file from a JSON snapshot.

    Args:
        snapshot:      Dict produced by docx_reader.read_docx().
        output_path:   Destination .docx path.
        template_path: Optional path to original DOCX used as style anchor.
                       When provided, its styles are inherited and any custom
                       styles from the original document are available.

    Returns:
        Absolute path of the written file.
    """
    if template_path and os.path.isfile(template_path):
        doc = Document(template_path)
        # Remove all body content from template, keep styles & sections
        body = doc.element.body
        for child in list(body):
            tag = child.tag
            if tag not in (qn("w:sectPr"),):
                body.remove(child)
    else:
        doc = Document()

    # Apply section layout from snapshot (first section only for simplicity)
    sections_data = snapshot.get("sections", [])
    if sections_data:
        sec = doc.sections[0]
        sd = sections_data[0]
        if sd.get("page_width_cm"):
            sec.page_width  = Cm(sd["page_width_cm"])
        if sd.get("page_height_cm"):
            sec.page_height = Cm(sd["page_height_cm"])
        if sd.get("margin_top_cm") is not None:
            sec.top_margin    = Cm(sd["margin_top_cm"])
        if sd.get("margin_bottom_cm") is not None:
            sec.bottom_margin = Cm(sd["margin_bottom_cm"])
        if sd.get("margin_left_cm") is not None:
            sec.left_margin   = Cm(sd["margin_left_cm"])
        if sd.get("margin_right_cm") is not None:
            sec.right_margin  = Cm(sd["margin_right_cm"])

    # Write body elements in order
    for element in snapshot.get("body", []):
        elem_type = element.get("type")
        if elem_type == "paragraph":
            _write_paragraph(doc, element)
        elif elem_type == "table":
            _write_table(doc, element)
        elif elem_type == "image":
            _write_image_placeholder(doc, element)

    out_dir = os.path.dirname(os.path.abspath(output_path))
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    doc.save(output_path)
    return os.path.abspath(output_path)


def write_docx_from_json_file(
    json_path: str,
    output_path: str,
    template_path: str | None = None,
) -> str:
    """
    Load a JSON snapshot from file and write it to a DOCX.

    Args:
        json_path:     Path to the .json snapshot file.
        output_path:   Destination .docx path.
        template_path: Optional original DOCX for style anchoring.

    Returns:
        Absolute path of the written DOCX.
    """
    if not os.path.isfile(json_path):
        raise FileNotFoundError(f"JSON snapshot not found: {json_path}")

    with open(json_path, "r", encoding="utf-8") as f:
        snapshot = json.load(f)

    return write_docx(snapshot, output_path, template_path)


def inject_content_into_docx(
    source_docx_path: str,
    spec: dict[str, Any],
    output_path: str | None = None,
) -> str:
    """
    Surgically inject paragraphs, runs, formatting, and images into an existing DOCX
    at a targeted location (e.g. after a heading), preserving 100% of existing styles,
    tables, headers/footers, and drawings.

    Args:
        source_docx_path: Path to source DOCX file.
        spec: Injection specification dict with keys:
              - "target_heading": str or pattern to match in paragraph text
              - "target_element_index": int (optional alternative to target_heading)
              - "replace_empty_after": bool (if True, clears blank paragraphs right after target)
              - "elements": list of element dicts to inject:
                  - type: "paragraph"
                  - style_name: optional style (defaults to "Normal")
                  - alignment: "LEFT"|"CENTER"|"RIGHT"|"JUSTIFY"
                  - space_before_pt, space_after_pt, left_indent_pt, first_line_indent_pt, line_spacing
                  - images: list of {path, width_cm, height_cm, gap}
                  - runs: list of {text, bold, italic, underline, strike, font_name, font_size, font_color}
        output_path: Destination DOCX path (defaults to overwriting source_docx_path).

    Returns:
        Absolute path of the saved DOCX.
    """
    if not os.path.isfile(source_docx_path):
        raise FileNotFoundError(f"Source DOCX not found: {source_docx_path}")

    doc = Document(source_docx_path)

    # Locate target paragraph: prioritize placeholder over target_heading
    target_idx: int | None = None
    is_placeholder_mode = False
    placeholder = spec.get("placeholder")
    target_heading = spec.get("target_heading")

    if placeholder:
        for i, p in enumerate(doc.paragraphs):
            if placeholder in p.text:
                target_idx = i
                is_placeholder_mode = True
                break

    if target_idx is None and target_heading:
        for i, p in enumerate(doc.paragraphs):
            if target_heading in p.text:
                target_idx = i
                break
    elif target_idx is None and spec.get("target_element_index") is not None:
        target_idx = int(spec["target_element_index"])

    if target_idx is None:
        target_desc = f"placeholder '{placeholder}'" if placeholder else f"heading '{target_heading}'"
        raise ValueError(f"Target {target_desc} not found in document")

    paragraphs_to_remove = []

    if is_placeholder_mode:
        # In placeholder mode: insert elements right before placeholder, then remove placeholder
        anchor_para = doc.paragraphs[target_idx]
        paragraphs_to_remove.append(anchor_para)
    else:
        # In heading mode: insert after target heading
        replace_empty = spec.get("replace_empty_after", False)
        curr_idx = target_idx + 1

        if replace_empty:
            while curr_idx < len(doc.paragraphs):
                p_next = doc.paragraphs[curr_idx]
                drawings = p_next._element.findall(".//" + qn("w:drawing"))
                if not p_next.text.strip() and not drawings:
                    paragraphs_to_remove.append(p_next)
                    curr_idx += 1
                else:
                    break

        anchor_para = doc.paragraphs[curr_idx] if curr_idx < len(doc.paragraphs) else None

    # Inject elements
    for el in spec.get("elements", []):
        elem_type = el.get("type", "paragraph")
        if elem_type == "paragraph":
            style_name = el.get("style_name", "Normal")
            style = _resolve_style(doc, style_name)
            if anchor_para is not None:
                p = anchor_para.insert_paragraph_before(style=style)
            else:
                p = doc.add_paragraph(style=style)

            _apply_paragraph_format(p, el)

            # Add images if specified
            for img_info in el.get("images", []):
                img_path = img_info.get("path")
                if not img_path:
                    continue
                if not os.path.isabs(img_path):
                    img_path = os.path.abspath(img_path)
                if not os.path.isfile(img_path):
                    raise FileNotFoundError(f"Image not found: {img_path}")

                w = Cm(img_info["width_cm"]) if img_info.get("width_cm") else None
                h = Cm(img_info["height_cm"]) if img_info.get("height_cm") else None
                r = p.add_run()
                r.add_picture(img_path, width=w, height=h)
                if img_info.get("gap", True):
                    p.add_run("   ")

            # Add runs
            for run_data in el.get("runs", []):
                r = p.add_run(run_data.get("text", ""))
                _apply_run_format(r, run_data)

            if not el.get("runs") and not el.get("images") and el.get("text"):
                p.add_run(el["text"])

    # Remove placeholder or empty paragraphs after inserting new elements
    for p_rem in paragraphs_to_remove:
        parent = p_rem._element.getparent()
        if parent is not None:
            parent.remove(p_rem._element)

    dest = os.path.abspath(output_path or source_docx_path)
    # Automatic backup if modifying in-place
    if dest == os.path.abspath(source_docx_path):
        bak_path = source_docx_path + ".bak"
        shutil.copy2(source_docx_path, bak_path)

    out_dir = os.path.dirname(dest)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    doc.save(dest)
    return dest


def inject_diagram_into_docx(
    source_docx_path: str | None = None,
    diagram_spec: dict[str, Any] | None = None,
    output_path: str | None = None,
    *,
    docx_path: str | None = None,
    png_path: str | None = None,
    heading: str | None = None,
    placeholder: str | None = None,
    caption: str | dict[str, Any] | None = None,
    width_cm: float | None = None,
    height_cm: float | None = None,
    max_height_cm: float | None = None,
) -> str:
    """
    Convenience wrapper to inject a diagram (image + caption + description) into a DOCX
    at a target location (placeholder or heading) with strict keepNext chaining.

    Supports both positional call:
        inject_diagram_into_docx(source_docx_path, diagram_spec, output_path)
    and keyword call:
        inject_diagram_into_docx(docx_path=..., png_path=..., heading=..., placeholder=..., caption=..., width_cm=...)

    Args:
        source_docx_path: Path to DOCX.
        diagram_spec: Dict containing image_path, width_cm, height_cm, placeholder, target_heading, caption_template.
        output_path: Optional output path.
    """
    doc_target = source_docx_path or docx_path
    if not doc_target:
        raise ValueError("Missing required DOCX path (source_docx_path or docx_path)")

    if diagram_spec is None:
        diagram_spec = {}
    else:
        diagram_spec = dict(diagram_spec)

    if png_path:
        diagram_spec.setdefault("image_path", png_path)
    if heading:
        diagram_spec.setdefault("target_heading", heading)
    if placeholder:
        diagram_spec.setdefault("placeholder", placeholder)
    if caption:
        diagram_spec.setdefault("caption_template", caption)
    if width_cm is not None:
        diagram_spec.setdefault("width_cm", width_cm)
    if height_cm is not None:
        diagram_spec.setdefault("height_cm", height_cm)
    elif max_height_cm is not None:
        diagram_spec.setdefault("height_cm", max_height_cm)

    image_path = diagram_spec.get("image_path")
    if not image_path or not os.path.isfile(image_path):
        raise FileNotFoundError(f"Diagram image not found: {image_path}")

    width_cm_val = diagram_spec.get("width_cm", 14.0)
    height_cm_val = diagram_spec.get("height_cm")

    cap_template = diagram_spec.get("caption_template")
    caption_text = ""
    description_text = ""
    cap_style: dict[str, Any] = {}
    desc_style: dict[str, Any] = {}

    if isinstance(cap_template, str):
        caption_text = cap_template
    elif isinstance(cap_template, dict):
        caption_text = cap_template.get("caption", "")
        description_text = cap_template.get("description", "")
        cap_style = cap_template.get("style", {})
        desc_style = cap_template.get("description_style", {})

    has_caption = bool(caption_text.strip())
    has_description = bool(description_text)

    elements: list[dict[str, Any]] = []

    # 1. Image paragraph (keepNext=True if caption or description follows)
    elements.append({
        "type": "paragraph",
        "alignment": "CENTER",
        "space_before_pt": 6,
        "space_after_pt": 4,
        "keep_next": has_caption or has_description,
        "images": [{
            "path": image_path,
            "width_cm": width_cm_val,
            "height_cm": height_cm_val,
        }],
    })

    # 2. Caption paragraph (keepNext=True if description follows)
    if has_caption:
        elements.append({
            "type": "paragraph",
            "alignment": cap_style.get("caption_alignment", "CENTER"),
            "space_before_pt": cap_style.get("space_before_pt", 4),
            "space_after_pt": cap_style.get("space_after_pt", 6 if has_description else 12),
            "keep_next": has_description,
            "runs": [{
                "text": caption_text,
                "bold": cap_style.get("caption_bold", False),
                "italic": cap_style.get("caption_italic", True),
                "font_name": cap_style.get("font_name", "Calibri"),
                "font_size": cap_style.get("caption_font_size", 10.0),
                "font_color": cap_style.get("caption_color", "#595959"),
            }],
        })

    # 3. Description paragraph(s) (keep_next=False on final paragraph)
    if has_description:
        desc_paragraphs = [description_text] if isinstance(description_text, str) else list(description_text)
        for d_idx, d_text in enumerate(desc_paragraphs):
            is_last = (d_idx == len(desc_paragraphs) - 1)
            elements.append({
                "type": "paragraph",
                "alignment": desc_style.get("alignment", "JUSTIFY"),
                "space_before_pt": desc_style.get("space_before_pt", 3),
                "space_after_pt": desc_style.get("space_after_pt", 12 if is_last else 4),
                "left_indent_pt": desc_style.get("left_indent_pt", 0),
                "keep_next": not is_last,
                "runs": [{
                    "text": d_text,
                    "bold": False,
                    "italic": False,
                    "font_name": desc_style.get("font_name", "Calibri"),
                    "font_size": desc_style.get("font_size", 10.5),
                    "font_color": desc_style.get("font_color", "#262626"),
                }],
            })

    injection_spec = {
        "placeholder": diagram_spec.get("placeholder"),
        "target_heading": diagram_spec.get("target_heading"),
        "target_element_index": diagram_spec.get("target_element_index"),
        "replace_empty_after": diagram_spec.get("replace_empty_after", False),
        "elements": elements,
    }

    return inject_content_into_docx(doc_target, injection_spec, output_path)



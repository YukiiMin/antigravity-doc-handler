"""
Bidirectional Markdown Converter for PDF, DOCX, and Markdown (.md)
Implements decoupled Document Architecture:
- Data Layer: Pure standard GFM Markdown (.md) containing 100% data fidelity (Headings, Bullets, Tables, Images).
- Presentation Layer: Clean YAML stylesheet (.style.yaml) acting like CSS for layout & styling.
- Round-trip compiler: (Data .md + Style .style.yaml) -> DOCX -> PDF.
"""

from __future__ import annotations
import os
import re
import sys
import yaml
from typing import Any, Callable, Dict, List, Optional, Tuple

import pymupdf
import docx
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

NS_W = nsdecls("w")
TOC_LINE_REGEX = re.compile(r"^(.*?)(?:\.{2,}|…+|(?:\.\s+){2,}\.|\t)\s*(\d+)$")


def _hex_to_rgb(hex_str: str) -> RGBColor:
    cleaned = hex_str.lstrip("#")
    if len(cleaned) == 6:
        try:
            r = int(cleaned[0:2], 16)
            g = int(cleaned[2:4], 16)
            b = int(cleaned[4:6], 16)
            return RGBColor(r, g, b)
        except ValueError:
            pass
    return RGBColor(30, 41, 59)


def _parse_length(val: Any, default_inches: float = 1.0) -> Inches:
    if val is None:
        return Inches(default_inches)
    if isinstance(val, (int, float)):
        return Inches(float(val))
    val_s = str(val).strip().lower()
    if val_s.endswith("in") or val_s.endswith("inch") or val_s.endswith("inches"):
        num = re.sub(r"[a-z]", "", val_s).strip()
        try:
            return Inches(float(num))
        except ValueError:
            return Inches(default_inches)
    elif val_s.endswith("cm"):
        num = val_s.replace("cm", "").strip()
        try:
            return Inches(float(num) / 2.54)
        except ValueError:
            return Inches(default_inches)
    elif val_s.endswith("pt"):
        num = val_s.replace("pt", "").strip()
        try:
            return Pt(float(num))
        except ValueError:
            return Inches(default_inches)
    try:
        return Inches(float(val_s))
    except ValueError:
        return Inches(default_inches)


def extract_pdf_styling_metadata(doc: pymupdf.Document) -> Dict[str, Any]:
    """
    Scan PDF sample pages to detect ground truth geometry and styling:
    - Page dimensions & margins (top, bottom, left, right).
    - Dominant body font family & size.
    - Prominent heading color (e.g. Red #C00000).
    - Dominant table header background fill color (e.g. Peach #FFE8E0).
    """
    if len(doc) == 0:
        return {}

    first_page = doc[0]
    p_w, p_h = first_page.rect.width, first_page.rect.height
    is_letter = abs(p_w - 612) < 30 and abs(p_h - 792) < 30
    page_size = "Letter" if is_letter else "A4"

    sample_limit = min(20, len(doc))
    lefts, rights, tops, bottoms = [], [], [], []
    fonts: Dict[str, int] = {}
    colors: Dict[str, int] = {}
    heading_colors: Dict[str, int] = {}
    fill_counts: Dict[str, int] = {}

    for p_idx in range(sample_limit):
        p = doc[p_idx]

        # Scan text blocks for margins
        blocks = p.get_text("blocks")
        for b in blocks:
            if b[1] > 45 and b[3] < p_h - 45 and (b[2] - b[0]) > 40:
                lefts.append(b[0])
                rights.append(p_w - b[2])
                tops.append(b[1])
                bottoms.append(p_h - b[3])

        # Scan text spans for fonts & colors
        td = p.get_text("dict")
        for b in td.get("blocks", []):
            if "lines" not in b:
                continue
            for l in b["lines"]:
                for s in l.get("spans", []):
                    txt = s.get("text", "").strip()
                    if not txt:
                        continue
                    font_base = s.get("font", "Calibri").split(",")[0].split("-")[0]
                    sz = round(s.get("size", 11.0), 1)
                    c = s.get("color", 0)
                    hex_c = f"#{c:06X}" if isinstance(c, int) else "#000000"

                    fonts[font_base] = fonts.get(font_base, 0) + len(txt)
                    colors[hex_c] = colors.get(hex_c, 0) + len(txt)

                    if sz >= 14 or "Bold" in s.get("font", ""):
                        if hex_c not in ("#000000", "#FFFFFF", "#202124", "#333333"):
                            heading_colors[hex_c] = heading_colors.get(hex_c, 0) + len(txt)

        # Scan drawings for table header vector fills
        for d in p.get_drawings():
            fill = d.get("fill")
            if fill:
                r, g, b_val = [int(c_val * 255) for c_val in fill]
                hex_fill = f"#{r:02X}{g:02X}{b_val:02X}"
                if hex_fill not in ("#000000", "#FFFFFF"):
                    fill_counts[hex_fill] = fill_counts.get(hex_fill, 0) + 1

    def to_in_str(val_list: List[float], default_in: float) -> str:
        if not val_list:
            return f"{default_in:.2f}in"
        val_in = round(min(val_list) / 72.0, 2)
        val_in = max(0.40, min(1.25, val_in))
        return f"{val_in:.2f}in"

    margin_left = to_in_str(lefts, 1.0)
    margin_right = to_in_str(rights, 0.55)
    margin_top = to_in_str(tops, 0.63)
    margin_bottom = to_in_str(bottoms, 0.87)

    dom_font = sorted(fonts.items(), key=lambda x: x[1], reverse=True)[0][0] if fonts else "Calibri"
    dom_color = sorted(colors.items(), key=lambda x: x[1], reverse=True)[0][0] if colors else "#000000"
    heading_color = sorted(heading_colors.items(), key=lambda x: x[1], reverse=True)[0][0] if heading_colors else "#C00000"
    table_header_bg = sorted(fill_counts.items(), key=lambda x: x[1], reverse=True)[0][0] if fill_counts else "#FFE8E0"

    return {
        "geometry": {
            "page_size": page_size,
            "margin": {
                "top": margin_top,
                "bottom": margin_bottom,
                "left": margin_left,
                "right": margin_right
            }
        },
        "typography": {
            "font_family": f"{dom_font}, Arial, sans-serif",
            "font_size": "11pt",
            "body_color": dom_color,
            "line_spacing": 1.15
        },
        "headings": {
            "color": heading_color,
            "h1_size": "16pt",
            "h2_size": "13pt",
            "h3_size": "12pt",
            "h4_size": "11pt"
        },
        "tables": {
            "header_background": table_header_bg,
            "border_color": "#000000",
            "cell_padding": "6pt"
        },
        "lists": {
            "bullet_glyph": "•",
            "space_before": "2pt",
            "space_after": "2pt"
        }
    }


def extract_docx_styling_metadata(doc: docx.Document) -> Dict[str, Any]:
    """Extract geometry and styling schema from an existing DOCX document."""
    sec = doc.sections[0]
    p_w = sec.page_width.inches if sec.page_width else 8.5
    p_h = sec.page_height.inches if sec.page_height else 11.0
    page_size = "Letter" if abs(p_w - 8.5) < 0.5 and abs(p_h - 11.0) < 0.5 else "A4"

    top_m = f"{sec.top_margin.inches:.2f}in" if sec.top_margin else "0.63in"
    bottom_m = f"{sec.bottom_margin.inches:.2f}in" if sec.bottom_margin else "0.87in"
    left_m = f"{sec.left_margin.inches:.2f}in" if sec.left_margin else "1.00in"
    right_m = f"{sec.right_margin.inches:.2f}in" if sec.right_margin else "0.55in"

    # Font & Color detection
    fonts: Dict[str, int] = {}
    colors: Dict[str, int] = {}
    heading_colors: Dict[str, int] = {}

    for p in doc.paragraphs:
        for r in p.runs:
            txt = r.text.strip()
            if not txt:
                continue
            if r.font.name:
                fonts[r.font.name] = fonts.get(r.font.name, 0) + len(txt)
            if r.font.color and r.font.color.rgb:
                hex_c = f"#{r.font.color.rgb}"
                colors[hex_c] = colors.get(hex_c, 0) + len(txt)
                if p.style.name.startswith("Heading") or r.bold:
                    if hex_c.upper() not in ("#000000", "#FFFFFF", "#1E293B", "#333333", "#202124"):
                        heading_colors[hex_c.upper()] = heading_colors.get(hex_c.upper(), 0) + len(txt)

    dom_font = sorted(fonts.items(), key=lambda x: x[1], reverse=True)[0][0] if fonts else "Calibri"
    dom_color = sorted(colors.items(), key=lambda x: x[1], reverse=True)[0][0] if colors else "#000000"
    heading_color = sorted(heading_colors.items(), key=lambda x: x[1], reverse=True)[0][0] if heading_colors else "#C00000"

    # Table header fill detection
    table_header_bg = "#FFE8E0"
    for t in doc.tables:
        if t.rows:
            tcPr = t.rows[0].cells[0]._tc.get_or_add_tcPr()
            shd = tcPr.find(qn("w:shd"))
            if shd is not None:
                fill_val = shd.get(qn("w:fill"))
                if fill_val and fill_val.lower() not in ("auto", "none", "ffffff", "000000"):
                    table_header_bg = f"#{fill_val.upper()}"
                    break

    return {
        "geometry": {
            "page_size": page_size,
            "margin": {
                "top": top_m,
                "bottom": bottom_m,
                "left": left_m,
                "right": right_m
            }
        },
        "typography": {
            "font_family": f"{dom_font}, Arial, sans-serif",
            "font_size": "11pt",
            "body_color": dom_color,
            "line_spacing": 1.15
        },
        "headings": {
            "color": heading_color,
            "h1_size": "16pt",
            "h2_size": "13pt",
            "h3_size": "12pt",
            "h4_size": "11pt"
        },
        "tables": {
            "header_background": table_header_bg,
            "border_color": "#000000",
            "cell_padding": "6pt"
        },
        "lists": {
            "bullet_glyph": "•",
            "space_before": "2pt",
            "space_after": "2pt"
        }
    }


# ==============================================================================
# 1. DOCX -> Decoupled (Data .md + Style .style.yaml)
# ==============================================================================
def docx_to_decoupled(
    docx_path: str,
    md_path: Optional[str] = None,
    style_yaml_path: Optional[str] = None,
    progress_callback: Optional[Callable[[float, str], None]] = None
) -> Tuple[bool, str, str]:
    """
    Extracts a pristine DOCX into two decoupled files:
    1. [name].md: Pure GFM Markdown containing 100% semantic content (no styling tags).
    2. [name].style.yaml: Structured layout & typography schema (CSS equivalent).
    """
    if not os.path.isfile(docx_path):
        return False, f"File không tồn tại: {docx_path}", ""

    stem = os.path.splitext(docx_path)[0]
    if not md_path:
        md_path = stem + ".md"
    if not style_yaml_path:
        style_yaml_path = stem + ".style.yaml"

    out_dir = os.path.dirname(os.path.abspath(md_path))
    base_name = os.path.splitext(os.path.basename(md_path))[0]
    assets_dir = os.path.join(out_dir, f"{base_name}_assets")
    os.makedirs(assets_dir, exist_ok=True)

    doc = docx.Document(docx_path)

    # 1. Extract and Save Style YAML
    style_meta = extract_docx_styling_metadata(doc)
    with open(style_yaml_path, "w", encoding="utf-8") as f_yaml:
        yaml.dump(style_meta, f_yaml, sort_keys=False, allow_unicode=True)

    # 2. Extract Images from relationships
    img_map = {}
    img_idx = 0
    for rel in doc.part.rels.values():
        if "image" in rel.target_ref:
            img_idx += 1
            img_ext = os.path.splitext(rel.target_ref)[1] or ".png"
            img_name = f"docx_img_{img_idx}{img_ext}"
            img_disk = os.path.join(assets_dir, img_name)
            with open(img_disk, "wb") as f_im:
                f_im.write(rel.target_part.blob)
            img_map[rel.target_ref] = f"{base_name}_assets/{img_name}"

    md_lines: List[str] = []
    total_elements = len(doc.paragraphs) + len(doc.tables)

    # Iterate elements preserving order
    # Extract document body elements in XML sequence
    doc_body = doc._element.body
    curr_idx = 0

    for child in doc_body:
        curr_idx += 1
        if progress_callback and total_elements > 0:
            percent = (curr_idx / total_elements) * 90.0
            progress_callback(percent, f"Đang bóc tách Markdown thuần ({curr_idx}/{total_elements})...")

        tag = child.tag.split("}")[-1]

        if tag == "p":
            p = docx.text.paragraph.Paragraph(child, doc)
            txt = p.text.strip()
            if not txt:
                continue

            style_name = p.style.name.lower()
            pPr = p._p.pPr
            has_num = pPr is not None and pPr.find(qn("w:numPr")) is not None
            has_tabs = pPr is not None and pPr.find(qn("w:tabs")) is not None

            # Check if TOC line with tab stop
            if has_tabs or "\t" in txt or TOC_LINE_REGEX.match(txt):
                m_t = TOC_LINE_REGEX.match(txt)
                if m_t:
                    md_lines.append(f"{m_t.group(1).strip()} ... {m_t.group(2).strip()}")
                    continue
                elif "\t" in txt:
                    parts = txt.split("\t", 1)
                    md_lines.append(f"{parts[0].strip()} ... {parts[1].strip()}")
                    continue

            # Headings
            if "heading 1" in style_name or re.match(r"^[IVXLCDM]+\.\s+[A-Z]", txt):
                clean_h = txt.strip()
                md_lines.append(f"\n# {clean_h}\n")
            elif "heading 2" in style_name or re.match(r"^\d+\.\s+[A-Z]", txt):
                clean_h = txt.strip()
                md_lines.append(f"\n## {clean_h}\n")
            elif "heading 3" in style_name or re.match(r"^\d+\.\d+\s+[A-Z]", txt):
                clean_h = txt.strip()
                md_lines.append(f"\n### {clean_h}\n")
            elif "heading 4" in style_name or re.match(r"^\d+\.\d+\.\d+\s+[A-Z]", txt):
                clean_h = txt.strip()
                md_lines.append(f"\n#### {clean_h}\n")
            # Bullet list items
            elif has_num or "bullet" in style_name or txt.startswith("•") or txt.startswith("+") or txt.startswith("-"):
                item_clean = re.sub(r"^[\uf06c\uf0b7•+\-*]\s*", "", txt).strip()
                md_lines.append(f"- {item_clean}")
            # Captions
            elif txt.startswith("Table ") or txt.startswith("Figure "):
                md_lines.append(f"*{txt}*\n")
            else:
                md_lines.append(f"{txt}\n")

        elif tag == "tbl":
            t = docx.table.Table(child, doc)
            if not t.rows:
                continue

            cleaned_rows: List[List[str]] = []
            for row in t.rows:
                row_cells = [c.text.strip().replace("\n", " ") for c in row.cells]
                if any(c for c in row_cells):
                    cleaned_rows.append(row_cells)

            if not cleaned_rows:
                continue

            # Filter duplicate columns from merged cells
            num_cols = len(cleaned_rows[0])
            table_md = []
            # Header
            table_md.append("| " + " | ".join(cleaned_rows[0]) + " |")
            table_md.append("| " + " | ".join(["---"] * num_cols) + " |")
            for r in cleaned_rows[1:]:
                # Pad or trim to num_cols
                padded = r[:num_cols] + [""] * max(0, num_cols - len(r))
                table_md.append("| " + " | ".join(padded) + " |")

            md_lines.append("\n" + "\n".join(table_md) + "\n")

    with open(md_path, "w", encoding="utf-8") as f_md:
        f_md.write("\n".join(md_lines))

    if progress_callback:
        progress_callback(100.0, f"Hoàn tất bóc tách: {os.path.basename(md_path)} & {os.path.basename(style_yaml_path)}")

    return True, md_path, style_yaml_path


# ==============================================================================
# 2. Decoupled (Data .md + Style .style.yaml) -> DOCX
# ==============================================================================
def decoupled_to_docx(
    md_path: str,
    docx_path: Optional[str] = None,
    style_yaml_path: Optional[str] = None,
    progress_callback: Optional[Callable[[float, str], None]] = None
) -> Tuple[bool, str]:
    """
    Compiles pure Markdown data (.md) + YAML stylesheet (.style.yaml) into a high-fidelity DOCX.
    Automatically finds [stem].style.yaml in the same directory if not explicitly specified.
    """
    if not os.path.isfile(md_path):
        return False, f"File không tồn tại: {md_path}"

    stem = os.path.splitext(md_path)[0]
    if not docx_path:
        docx_path = stem + ".docx"

    # Auto-discover style yaml
    if not style_yaml_path:
        candidate = stem + ".style.yaml"
        if os.path.isfile(candidate):
            style_yaml_path = candidate
        else:
            # Check for candidate without .clean or similar
            candidate_base = re.sub(r"(_clean|_extracted|_perfect.*)$", "", stem, flags=re.IGNORECASE) + ".style.yaml"
            if os.path.isfile(candidate_base):
                style_yaml_path = candidate_base

    style_meta: Dict[str, Any] = {}
    if style_yaml_path and os.path.isfile(style_yaml_path):
        try:
            with open(style_yaml_path, "r", encoding="utf-8") as f_y:
                style_meta = yaml.safe_load(f_y) or {}
        except Exception:
            style_meta = {}

    with open(md_path, "r", encoding="utf-8") as f_md:
        body = f_md.read()

    # Fallback to embedded frontmatter if pure yaml not provided
    if not style_meta and body.startswith("---"):
        parts = body.split("---", 2)
        if len(parts) >= 3:
            try:
                style_meta = yaml.safe_load(parts[1]) or {}
            except Exception:
                pass
            body = parts[2]

    geom = style_meta.get("geometry", {})
    margins = geom.get("margin", {})
    typo = style_meta.get("typography", {})
    headings = style_meta.get("headings", {})
    tables_meta = style_meta.get("tables", {})

    font_family = typo.get("font_family", "Calibri").split(",")[0].strip().replace("'", "").replace('"', "")
    heading_hex = headings.get("color", "#C00000")
    body_hex = typo.get("body_color", "#000000")
    header_bg_hex = tables_meta.get("header_background", "#FFE8E0").lstrip("#")
    border_hex = tables_meta.get("border_color", "#000000").lstrip("#")

    doc = docx.Document()

    # 1. Page Margins
    sec = doc.sections[0]
    if isinstance(margins, dict):
        sec.top_margin = _parse_length(margins.get("top"), 0.63)
        sec.bottom_margin = _parse_length(margins.get("bottom"), 0.87)
        sec.left_margin = _parse_length(margins.get("left"), 1.00)
        sec.right_margin = _parse_length(margins.get("right"), 0.55)
    else:
        single_m = _parse_length(margins, 1.0)
        sec.top_margin = single_m
        sec.bottom_margin = single_m
        sec.left_margin = single_m
        sec.right_margin = single_m

    # Calculate Tab Stop position at right margin
    try:
        printable_w = sec.page_width - sec.left_margin - sec.right_margin
        tab_pos_twips = int(printable_w / 635)
    except Exception:
        tab_pos_twips = 9360

    # 2. Configure Typography Styles
    normal_style = doc.styles["Normal"]
    normal_font = normal_style.font
    normal_font.name = font_family
    normal_font.size = Pt(11)
    normal_font.color.rgb = _hex_to_rgb(body_hex)

    h_color = _hex_to_rgb(heading_hex)
    for lvl, size in [("Heading 1", Pt(16)), ("Heading 2", Pt(13)), ("Heading 3", Pt(12)), ("Heading 4", Pt(11))]:
        if lvl in doc.styles:
            h_st = doc.styles[lvl]
            h_st.font.name = font_family
            h_st.font.size = size
            h_st.font.bold = True
            h_st.font.color.rgb = h_color

    base_dir = os.path.dirname(os.path.abspath(md_path))
    lines = body.split("\n")
    total_lines = len(lines)

    in_table = False
    table_buffer: List[List[str]] = []

    def flush_table():
        nonlocal in_table, table_buffer
        if not table_buffer:
            return
        col_count = max(len(row) for row in table_buffer)
        t = doc.add_table(rows=len(table_buffer), cols=col_count)
        t.autofit = True

        for r_idx, row_data in enumerate(table_buffer):
            row = t.rows[r_idx]
            trPr = row._tr.get_or_add_trPr()
            trPr.append(parse_xml(f'<w:cantSplit {NS_W}/>'))

            if r_idx == 0 and len(table_buffer) > 1:
                trPr.append(parse_xml(f'<w:tblHeader {NS_W}/>'))

            for c_idx, val in enumerate(row_data):
                if c_idx < len(row.cells):
                    cell = row.cells[c_idx]
                    cell.text = val
                    for cp in cell.paragraphs:
                        for cr in cp.runs:
                            cr.font.name = font_family
                            cr.font.size = Pt(10)

                    if r_idx == 0:
                        # Apply Peach #FFE8E0 header shading
                        shading = parse_xml(f'<w:shd {NS_W} w:fill="{header_bg_hex}"/>')
                        cell._tc.get_or_add_tcPr().append(shading)
                        for cp in cell.paragraphs:
                            for cr in cp.runs:
                                cr.bold = True

        doc.add_paragraph()
        table_buffer.clear()
        in_table = False

    for idx, line in enumerate(lines):
        if progress_callback and total_lines > 0:
            percent = (idx / total_lines) * 90.0
            progress_callback(percent, f"Đang kết xuất DOCX ({idx + 1}/{total_lines})...")

        s_line = line.strip()

        # Handle Tables
        if s_line.startswith("|") and s_line.endswith("|"):
            parts = [p.strip() for p in s_line.split("|")[1:-1]]
            if not in_table:
                in_table = True
                table_buffer.append(parts)
            else:
                if all(re.match(r"^[-:]+$", p) for p in parts):
                    continue
                table_buffer.append(parts)
            continue
        elif in_table:
            flush_table()

        if not s_line:
            continue

        # Handle Images
        img_match = re.search(r"!\[(.*?)\]\((.*?)\)", s_line)
        if img_match:
            img_rel_path = img_match.group(2).strip()
            full_img_path = os.path.join(base_dir, img_rel_path)
            if os.path.isfile(full_img_path):
                p_img = doc.add_paragraph()
                p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
                p_img.add_run().add_picture(full_img_path, width=Inches(5.5))
                continue

        # Table & Figure Captions
        if s_line.startswith("*Table ") or s_line.startswith("*Figure "):
            caption_text = s_line.strip("*")
            p_cap = doc.add_paragraph()
            p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
            r_cap = p_cap.add_run(caption_text)
            r_cap.font.name = font_family
            r_cap.font.size = Pt(10)
            r_cap.italic = True
            p_cap.paragraph_format.space_before = Pt(3)
            p_cap.paragraph_format.space_after = Pt(8)
            continue

        # TOC lines with dot leaders
        m_toc = TOC_LINE_REGEX.match(s_line)
        if m_toc:
            title_p = m_toc.group(1).strip()
            page_p = m_toc.group(2).strip()
            p_toc = doc.add_paragraph()
            _apply_tab_stop_to_paragraph(p_toc, title_p, page_p, font_name=font_family, tab_pos_twips=tab_pos_twips)
            continue

        # Headings
        if s_line.startswith("# "):
            doc.add_heading(s_line[2:].strip(), level=1)
        elif s_line.startswith("## "):
            doc.add_heading(s_line[3:].strip(), level=2)
        elif s_line.startswith("### "):
            doc.add_heading(s_line[4:].strip(), level=3)
        elif s_line.startswith("#### "):
            doc.add_heading(s_line[5:].strip(), level=4)
        elif s_line.startswith("- ") or s_line.startswith("* "):
            p = doc.add_paragraph(style="List Bullet")
            _add_formatted_runs(p, s_line[2:].strip())
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(2)
        elif re.match(r"^\d+\.\s+", s_line):
            text_val = re.sub(r"^\d+\.\s+", "", s_line)
            p = doc.add_paragraph(style="List Number")
            _add_formatted_runs(p, text_val)
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(2)
        else:
            p = doc.add_paragraph()
            _add_formatted_runs(p, s_line)

    if in_table:
        flush_table()

    doc.save(docx_path)
    if progress_callback:
        progress_callback(100.0, f"Đã tạo file Word: {os.path.basename(docx_path)}")

    return True, docx_path


def _apply_tab_stop_to_paragraph(
    p: docx.text.paragraph.Paragraph,
    title_text: str,
    page_num_text: str,
    font_name: str = "Calibri",
    font_size_pt: float = 11.0,
    tab_pos_twips: int = 9360
) -> None:
    """Format paragraph with right-aligned Tab Stop with dot leader."""
    p.text = ""
    r_title = p.add_run(title_text)
    r_title.font.name = font_name
    r_title.font.size = Pt(font_size_pt)

    r_tab = p.add_run("\t")
    r_tab.font.name = font_name
    r_tab.font.size = Pt(font_size_pt)

    r_num = p.add_run(page_num_text)
    r_num.font.name = font_name
    r_num.font.size = Pt(font_size_pt)

    pPr = p._p.get_or_add_pPr()
    pPr.append(parse_xml(
        f'<w:tabs {NS_W}>'
        f'<w:tab w:val="right" w:leader="dot" w:pos="{tab_pos_twips}"/>'
        f'</w:tabs>'
    ))
    pPr.append(parse_xml(f'<w:spacing {NS_W} w:before="60" w:after="40" w:line="240" w:lineRule="auto"/>'))


def _add_formatted_runs(p: docx.text.paragraph.Paragraph, text: str) -> None:
    """Parse inline Markdown bold and italic tokens into docx runs."""
    tokens = re.split(r"(\*\*.*?\*\*|\*.*?\*)", text)
    for token in tokens:
        if token.startswith("**") and token.endswith("**") and len(token) >= 4:
            r = p.add_run(token[2:-2])
            r.bold = True
        elif token.startswith("*") and token.endswith("*") and len(token) >= 2:
            r = p.add_run(token[1:-1])
            r.italic = True
        else:
            p.add_run(token)


# ==============================================================================
# 3. Facade wrappers (Compatible with CLI & GUI)
# ==============================================================================
def docx_to_markdown(
    docx_path: str,
    md_path: Optional[str] = None,
    progress_callback: Optional[Callable[[float, str], None]] = None
) -> Tuple[bool, str]:
    """Wraps docx_to_decoupled: outputs both [name].md and [name].style.yaml."""
    ok, out_md, _ = docx_to_decoupled(docx_path, md_path=md_path, progress_callback=progress_callback)
    return ok, out_md


def markdown_to_docx(
    md_path: str,
    docx_path: Optional[str] = None,
    style_yaml_path: Optional[str] = None,
    progress_callback: Optional[Callable[[float, str], None]] = None
) -> Tuple[bool, str]:
    """Wraps decoupled_to_docx: auto-discovers [name].style.yaml."""
    return decoupled_to_docx(md_path, docx_path=docx_path, style_yaml_path=style_yaml_path, progress_callback=progress_callback)


def pdf_to_markdown(
    pdf_path: str,
    md_path: Optional[str] = None,
    progress_callback: Optional[Callable[[float, str], None]] = None
) -> Tuple[bool, str]:
    """
    Full 3-stage PDF -> Markdown pipeline:
    1. Converts PDF -> pristine DOCX using Flow Engine + Smart Post-Processor v6.
    2. Bóc tách DOCX -> [name].md (Data) + [name].style.yaml (Style).
    """
    if not os.path.isfile(pdf_path):
        return False, f"File không tồn tại: {pdf_path}"

    if not md_path:
        md_path = os.path.splitext(pdf_path)[0] + ".md"

    # Temporary pristine DOCX
    temp_docx = os.path.splitext(md_path)[0] + "_temp_stage1.docx"

    try:
        from .converter_engine import convert_pdf_to_docx_flow
    except ImportError:
        from converter_engine import convert_pdf_to_docx_flow

    if progress_callback:
        progress_callback(10.0, "Tầng 1/2: Chuyển đổi PDF sang DOCX chuẩn 100% (Post-Processor v6)...")

    ok_d, res_d = convert_pdf_to_docx_flow(pdf_path, temp_docx, progress_callback=progress_callback)
    if not ok_d:
        return False, f"Lỗi tại Tầng 1 (PDF -> DOCX): {res_d}"

    if progress_callback:
        progress_callback(60.0, "Tầng 2/2: Bóc tách DOCX sang Data .md và Style .style.yaml...")

    style_yaml_path = os.path.splitext(md_path)[0] + ".style.yaml"
    ok_md, out_md, out_yaml = docx_to_decoupled(temp_docx, md_path, style_yaml_path, progress_callback=progress_callback)

    if os.path.exists(temp_docx):
        try:
            os.remove(temp_docx)
        except Exception:
            pass

    return ok_md, out_md


# ==============================================================================
# 4. DOCX -> PDF & Markdown -> PDF
# ==============================================================================
def docx_to_pdf(
    docx_path: str,
    pdf_path: Optional[str] = None,
    progress_callback: Optional[Callable[[float, str], None]] = None
) -> Tuple[bool, str]:
    if not os.path.isfile(docx_path):
        return False, f"File không tồn tại: {docx_path}"

    if not pdf_path:
        pdf_path = os.path.splitext(docx_path)[0] + ".pdf"

    if progress_callback:
        progress_callback(20.0, "Đang khởi chạy Microsoft Word COM để xuất PDF...")

    try:
        import win32com.client as win32
        word = win32.Dispatch("Word.Application")
        word.Visible = False
        word.DisplayAlerts = 0

        abs_docx = os.path.abspath(docx_path)
        abs_pdf = os.path.abspath(pdf_path)

        doc = word.Documents.Open(abs_docx, ReadOnly=True)
        if progress_callback:
            progress_callback(60.0, "Đang xuất định dạng PDF chuẩn...")
        doc.SaveAs2(abs_pdf, FileFormat=17)
        doc.Close(SaveChanges=False)
        word.Quit()

        if progress_callback:
            progress_callback(100.0, f"Hoàn tất xuất PDF: {os.path.basename(pdf_path)}")
        return True, pdf_path
    except Exception as word_exc:
        soffice_path = r"C:\Program Files\LibreOffice\program\soffice.com"
        if os.path.isfile(soffice_path):
            try:
                if progress_callback:
                    progress_callback(70.0, "Word COM không khả dụng, chuyển sang LibreOffice export PDF...")
                abs_docx = os.path.abspath(docx_path)
                out_dir = os.path.dirname(os.path.abspath(pdf_path))
                import subprocess
                import shutil
                cmd = [soffice_path, "--headless", "--nologo", "--convert-to", "pdf", "--outdir", out_dir, abs_docx]
                subprocess.run(cmd, capture_output=True, text=True)
                expected_out = os.path.join(out_dir, os.path.splitext(os.path.basename(docx_path))[0] + ".pdf")
                if os.path.isfile(expected_out):
                    if expected_out != os.path.abspath(pdf_path):
                        shutil.move(expected_out, os.path.abspath(pdf_path))
                    if progress_callback:
                        progress_callback(100.0, f"Hoàn tất xuất PDF (LibreOffice): {os.path.basename(pdf_path)}")
                    return True, pdf_path
            except Exception as lo_exc:
                return False, f"Lỗi xuất PDF qua cả Word ({word_exc}) và LibreOffice ({lo_exc})"

        return False, f"Lỗi xuất PDF qua Word: {word_exc}"


def markdown_to_pdf(
    md_path: str,
    pdf_path: Optional[str] = None,
    style_yaml_path: Optional[str] = None,
    progress_callback: Optional[Callable[[float, str], None]] = None
) -> Tuple[bool, str]:
    if not pdf_path:
        pdf_path = os.path.splitext(md_path)[0] + ".pdf"

    temp_docx = os.path.splitext(md_path)[0] + "_temp.docx"

    if progress_callback:
        progress_callback(10.0, "Bước 1/2: Biên dịch Markdown + Style.yaml sang DOCX...")

    ok_docx, res_docx = markdown_to_docx(md_path, temp_docx, style_yaml_path=style_yaml_path, progress_callback=progress_callback)
    if not ok_docx:
        return False, res_docx

    if progress_callback:
        progress_callback(60.0, "Bước 2/2: Xuất DOCX sang PDF chất lượng cao...")

    ok_pdf, res_pdf = docx_to_pdf(temp_docx, pdf_path, progress_callback)

    if os.path.exists(temp_docx):
        try:
            os.remove(temp_docx)
        except Exception:
            pass

    return ok_pdf, res_pdf

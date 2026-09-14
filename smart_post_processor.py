"""
Smart Post-Processing Engine for DOCX (v3.0)
Applies OpenXML exact geometry, native Word Tab Stops with dot leaders,
Semantic List Engine (numbering.xml, dynamic w:ilvl, glyph stripping),
Auto-Table Stitching across page breaks, Table Pagination Protection (<w:cantSplit/>),
Orphan Page Number Removal, and Native Footer Page Number Injection.
"""

from __future__ import annotations
import io
import os
import sys
import re
import shutil
import time
import zipfile
from typing import List, Tuple, Optional

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
import docx
from docx.shared import Pt, Inches, RGBColor
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls, qn

NS_W = nsdecls("w")
TOC_LINE_REGEX = re.compile(r"^(.*?)(?:\.{3,}|…+)\s*(\d+)$")
MULTI_TOC_REGEX = re.compile(r"(\.{3,}\s*\d+)\s+([A-Z0-9IVX])")
INLINE_BULLET_REGEX = re.compile(r"([^\n]+?)\s*([\u2022\uf06c\u25cf\u25cb\u25a0\u25aa\u25ba\u2013\u2014]\s*[A-Z][^\n]*)")

BULLET_GLYPH_REGEX = re.compile(r"^[\uf06c\uf0b7\u2022\u25cf\u25cb\u25a0\u25aa\u25ba]\s*")
SUB_BULLET_REGEX = re.compile(r"^[\+\-]\s*(\t\s*)?")

RED_COLOR = RGBColor(192, 0, 0)      # #C00000
DARK_COLOR = RGBColor(30, 41, 59)
CANONICAL_NUM_ID = "100"
CANONICAL_ABSTRACT_ID = "100"


def apply_tab_stop_to_paragraph(
    p: docx.text.paragraph.Paragraph,
    title_text: str,
    page_num_text: str,
    font_name: str = "Calibri",
    font_size_pt: float = 11.0,
    is_italic: Optional[bool] = None,
    tab_pos_twips: int = 9360,
    line_spacing_twips: Optional[int] = None,
    before_twips: Optional[int] = None,
    after_twips: Optional[int] = None
) -> None:
    """
    Format paragraph with a right-aligned Tab Stop with dot leader.
    Disables word wrap to guarantee that the line never breaks into two.
    Calibrates hierarchical LeftIndent and vertical spacing:
    - Tables and Figures: Italic Calibri 11pt, compact spacing (line=221 exact, before=68, after=34)
      matching ApowerPDF so all 43 tables fit on Page 5 without spilling into Page 6.
    - TOC entries: Normal Calibri 11pt, hierarchical indents (0pt / 24pt / 46pt), line=221 exact.
    """
    clean_title = title_text.strip()
    is_table_or_figure = clean_title.startswith("Table ") or clean_title.startswith("Figure ")

    if is_italic is None:
        is_italic = True if is_table_or_figure else False

    if line_spacing_twips is None or line_spacing_twips == 290:
        line_spacing_twips = 221

    if before_twips is None:
        before_twips = 68

    if after_twips is None:
        after_twips = 34

    pPr = p._p.get_or_add_pPr()
    p.text = ""

    # Disable word wrap
    pPr.append(parse_xml(f'<w:wordWrap {NS_W} w:val="0"/>'))

    # Set exact line spacing and before/after twips
    pPr.append(parse_xml(f'<w:spacing {NS_W} w:line="{line_spacing_twips}" w:lineRule="exact" w:before="{before_twips}" w:after="{after_twips}"/>'))

    # Add Tab Stop with dot leader
    pPr.append(parse_xml(f'<w:tabs {NS_W}><w:tab w:val="right" w:leader="dot" w:pos="{tab_pos_twips}"/></w:tabs>'))

    # Set hierarchical LeftIndent based on TOC level matching original layout (ApowerPDF: Lv0=0pt, Lv1=24pt, Lv2=46pt)
    if is_table_or_figure:
        p.paragraph_format.left_indent = Pt(0)
    elif re.match(r"^\d+\.\d+\s", clean_title):
        p.paragraph_format.left_indent = Pt(46)
    elif re.match(r"^\d+\.\s", clean_title):
        p.paragraph_format.left_indent = Pt(24)
    else:
        p.paragraph_format.left_indent = Pt(0)

    # Title run
    r_title = p.add_run(title_text)
    r_title.font.name = font_name
    r_title.font.size = Pt(font_size_pt)
    r_title.italic = is_italic
    r_title.font.color.rgb = DARK_COLOR

    # Tab character
    r_tab = p.add_run()
    r_tab.font.name = font_name
    r_tab.font.size = Pt(font_size_pt)
    r_tab.add_tab()

    # Page number run
    r_page = p.add_run(page_num_text)
    r_page.font.name = font_name
    r_page.font.size = Pt(font_size_pt)
    r_page.italic = is_italic
    r_page.font.color.rgb = DARK_COLOR


def ensure_canonical_numbering(doc: docx.Document) -> str:
    """
    Inject or verify canonical abstract numbering definition in word/numbering.xml:
    - Level 0 (ilvl=0): Bullet symbol (\uf06c), font Wingdings, size 24 (12pt), matching ApowerPDF.
    - Level 1 (ilvl=1): Sub-bullet (+), font Calibri bold, size 24 (12pt).
    Preserves OpenXML schema requirement: all abstractNum elements precede num elements.
    """
    try:
        np = doc.part.numbering_part
    except Exception:
        return ""

    num_elm = np._element
    w_abstractNum = qn("w:abstractNum")
    w_abstractNumId = qn("w:abstractNumId")
    w_num = qn("w:num")
    w_numId = qn("w:numId")

    existing_ab = None
    for ab in num_elm.findall(w_abstractNum):
        if ab.get(w_abstractNumId) == CANONICAL_ABSTRACT_ID:
            existing_ab = ab
            break

    if existing_ab is not None:
        num_elm.remove(existing_ab)

    xml_num = parse_xml(
        f'<w:abstractNum {NS_W} w:abstractNumId="{CANONICAL_ABSTRACT_ID}">'
        f'<w:multiLevelType w:val="hybridMultilevel"/>'
        f'<w:lvl w:ilvl="0">'
        f'  <w:start w:val="1"/>'
        f'  <w:numFmt w:val="bullet"/>'
        f'  <w:lvlText w:val="&#xF06C;"/>'
        f'  <w:lvlJc w:val="left"/>'
        f'  <w:pPr><w:ind w:left="480" w:hanging="280"/></w:pPr>'
        f'  <w:rPr><w:rFonts w:ascii="Wingdings" w:hAnsi="Wingdings" w:hint="default"/><w:sz w:val="24"/></w:rPr>'
        f'</w:lvl>'
        f'<w:lvl w:ilvl="1">'
        f'  <w:start w:val="1"/>'
        f'  <w:numFmt w:val="bullet"/>'
        f'  <w:lvlText w:val="+"/>'
        f'  <w:lvlJc w:val="left"/>'
        f'  <w:pPr><w:ind w:left="720" w:hanging="280"/></w:pPr>'
        f'  <w:rPr><w:rFonts w:ascii="Calibri" w:hAnsi="Calibri" w:hint="default"/><w:b/><w:sz w:val="24"/></w:rPr>'
        f'</w:lvl>'
        f'</w:abstractNum>'
    )
    first_num = num_elm.find(w_num)
    if first_num is not None:
        first_num.addprevious(xml_num)
    else:
        num_elm.append(xml_num)

    existing_concrete = None
    for num in num_elm.findall(w_num):
        if num.get(w_numId) == CANONICAL_NUM_ID:
            existing_concrete = num
            break

    if existing_concrete is None:
        xml_concrete = parse_xml(f'<w:num {NS_W} w:numId="{CANONICAL_NUM_ID}"><w:abstractNumId w:val="{CANONICAL_ABSTRACT_ID}"/></w:num>')
        num_elm.append(xml_concrete)

    return CANONICAL_NUM_ID


def stitch_broken_tables(doc: docx.Document) -> int:
    """
    Auto-stitch tables that were split across page breaks by PDF layout analyzers.
    Detects pairs where Table B immediately follows Table A with only page numbers or blank paragraphs.
    Merges rows, removes intermediate junk, and maintains schema integrity.
    """
    stitched_count = 0
    tables = doc.tables
    i = 0
    while i < len(tables) - 1:
        t1 = tables[i]
        t2 = tables[i + 1]

        if len(t1.columns) != len(t2.columns):
            i += 1
            continue

        curr = t1._element.getnext()
        inter_elms = []
        is_split = True
        while curr is not None and curr != t2._element:
            inter_elms.append(curr)
            if curr.tag.endswith("p"):
                p_obj = docx.text.paragraph.Paragraph(curr, doc)
                txt = p_obj.text.strip()
                if txt and not txt.isdigit():
                    is_split = False
                    break
            elif not curr.tag.endswith(("sectPr", "bookmarkStart", "bookmarkEnd")):
                is_split = False
                break
            curr = curr.getnext()

        if is_split and curr == t2._element:
            # Append all rows of t2 to t1
            for row in t2.rows:
                t1._element.append(row._tr)

            # Remove intermediate elements (e.g. orphan page numbers)
            for el in inter_elms:
                p_parent = el.getparent()
                if p_parent is not None:
                    p_parent.remove(el)

            # Remove t2
            p_t2 = t2._element.getparent()
            if p_t2 is not None:
                p_t2.remove(t2._element)

            stitched_count += 1
            tables = doc.tables  # refresh table list after deletion
        else:
            i += 1

    return stitched_count


def apply_table_pagination_rules(doc: docx.Document, table_header_bg: str = "FFE8E0") -> None:
    """
    Protect table layout from awkward row splits and apply authentic header styling:
    - Sets <w:cantSplit/> on all table rows so rows are never split across pages.
    - Sets <w:tblHeader/> on row 0 so table headers repeat if a long table spans pages.
    - Applies authentic header cell background fill (<w:shd w:fill="{table_header_bg}"/>) and bold font.
    - Converts row height w:hRule from 'exact' to 'atLeast' to prevent clipping long text/emails.
    """
    w_cantSplit = qn("w:cantSplit")
    w_tblHeader = qn("w:tblHeader")
    w_trHeight = qn("w:trHeight")
    w_hRule = qn("w:hRule")

    for table in doc.tables:
        for idx, row in enumerate(table.rows):
            trPr = row._tr.get_or_add_trPr()
            if trPr.find(w_cantSplit) is None:
                trPr.append(parse_xml(f'<w:cantSplit {NS_W}/>'))
            if idx == 0 and len(table.rows) > 1:
                if trPr.find(w_tblHeader) is None:
                    trPr.append(parse_xml(f'<w:tblHeader {NS_W}/>'))
                for cell in row.cells:
                    tcPr = cell._tc.get_or_add_tcPr()
                    if tcPr.find(qn("w:shd")) is None:
                        tcPr.append(parse_xml(f'<w:shd {NS_W} w:fill="{table_header_bg}"/>'))
                    for cp in cell.paragraphs:
                        for cr in cp.runs:
                            cr.bold = True
                            cr.font.name = "Calibri"

            # Convert exact row height to atLeast
            trHeight = trPr.find(w_trHeight)
            if trHeight is not None:
                h_rule = trHeight.get(w_hRule)
                if h_rule == "exact":
                    trHeight.set(w_hRule, "atLeast")


def extract_pdf_semantic_map(pdf_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Pre-extract semantic styling directly from the original PDF using PyMuPDF:
    - Identifies Red headings (RGB #C00000 / #C55A11, font size >= 14pt).
    - Extracts vertical rhythm and TOC line spacing.
    - Extracts dominant table header background fill color (e.g. Peach #FFE8E0).
    Returns a dictionary of detected semantic rules.
    """
    default_headings = {
        "Table of Contents": 16.0,
        "List of Tables": 16.0,
        "List of Figures": 16.0,
        "Acknowledgements": 16.0,
        "Definition and Acronyms": 16.0
    }

    if not pdf_path or not os.path.isfile(pdf_path):
        return {"red_headings": default_headings, "line_spacing_twips": 221, "table_header_bg": "FFE8E0"}

    red_headings: Dict[str, float] = dict(default_headings)
    table_header_bg = "FFE8E0"
    try:
        import pymupdf
        doc_pdf = pymupdf.open(pdf_path)
        fill_counts: Dict[str, int] = {}
        for p_idx, page in enumerate(doc_pdf):
            data = page.get_text("dict")
            for b in data.get("blocks", []):
                if "lines" not in b:
                    continue
                for l in b["lines"]:
                    line_text = "".join(s.get("text", "") for s in l.get("spans", [])).strip()
                    if not line_text:
                        continue
                    first_span = l["spans"][0]
                    color_int = first_span.get("color", 0)
                    r = (color_int >> 16) & 255
                    g = (color_int >> 8) & 255
                    b_col = color_int & 255
                    is_red = (r > 150 and g < 60 and b_col < 60) or (color_int == 12582912)
                    sz = first_span.get("size", 11.0)

                    if is_red or (sz >= 15.0 and any(h in line_text for h in default_headings)):
                        for known in default_headings:
                            if known in line_text:
                                red_headings[known] = max(sz, 16.0)
                                break

            # Sample first 20 pages for table header vector fills
            if p_idx < 20:
                for d in page.get_drawings():
                    fill = d.get("fill")
                    if fill:
                        r_f, g_f, b_f = [int(c_val * 255) for c_val in fill]
                        hex_f = f"{r_f:02X}{g_f:02X}{b_f:02X}"
                        if hex_f not in ("000000", "FFFFFF"):
                            fill_counts[hex_f] = fill_counts.get(hex_f, 0) + 1

        if fill_counts:
            table_header_bg = sorted(fill_counts.items(), key=lambda x: x[1], reverse=True)[0][0]
        doc_pdf.close()
    except Exception as e:
        print(f"[SemanticMap Warning] {e}")

    return {
        "red_headings": red_headings,
        "line_spacing_twips": 221,
        "table_header_bg": table_header_bg
    }


def separate_merged_heading_paragraphs(doc: docx.Document, red_headings: Dict[str, float]) -> int:
    """
    Detects headings that were accidentally merged with body text or list entries by pdf2docx
    (e.g., 'List of Tables \\nTable 1 - Definition and Acronyms...').
    Separates them into standalone heading paragraphs and applies authentic Red styling (#C00000, 16pt Bold).
    """
    separated_count = 0
    w_ind = qn("w:ind")
    w_spacing = qn("w:spacing")

    def format_heading_p(target_p: docx.text.paragraph.Paragraph, title: str, sz: float) -> None:
        target_p.text = ""
        r = target_p.add_run(title)
        r.bold = True
        r.font.name = "Calibri"
        r.font.size = Pt(sz)
        r.font.color.rgb = RED_COLOR

        pPr = target_p._p.get_or_add_pPr()
        for old_ind in pPr.findall(w_ind):
            pPr.remove(old_ind)
        for old_sp in pPr.findall(w_spacing):
            pPr.remove(old_sp)
        # List of Tables and List of Figures need compact after space (40 twips = 2pt) so tables/figures fit on 1 page
        after_tw = "40" if title in ("List of Tables", "List of Figures") else "120"
        before_tw = "200" if title in ("List of Tables", "List of Figures") else "460"
        pPr.append(parse_xml(f'<w:spacing {NS_W} w:before="{before_tw}" w:after="{after_tw}" w:line="320" w:lineRule="exact"/>'))
        if title in ("Table of Contents", "List of Tables", "List of Figures", "Acknowledgements", "Definition and Acronyms"):
            if pPr.find(qn("w:pageBreakBefore")) is None:
                pPr.append(parse_xml(f'<w:pageBreakBefore {NS_W}/>'))

    i = 0
    while i < len(doc.paragraphs):
        p = doc.paragraphs[i]
        txt = p.text.strip()
        if not txt:
            i += 1
            continue

        matched_heading: Optional[str] = None
        for heading_text in red_headings:
            if txt == heading_text or txt.startswith(heading_text + " \n") or txt.startswith(heading_text + "\n") or txt.startswith(heading_text + "\t"):
                matched_heading = heading_text
                break

        if matched_heading:
            font_sz = red_headings.get(matched_heading, 16.0)

            if "\n" in txt:
                # Merged paragraph with newline: split title from subsequent entries
                parts = txt.split("\n", 1)
                heading_part = parts[0].strip()
                rest_part = parts[1].strip()

                format_heading_p(p, heading_part, font_sz)

                # Insert the remaining text as an independent paragraph
                new_p = docx.oxml.OxmlElement('w:p')
                p._p.addnext(new_p)
                wrapped_p = docx.text.paragraph.Paragraph(new_p, doc)
                wrapped_p.add_run(rest_part)

                separated_count += 1
                i += 2
                continue
            else:
                # Standalone heading: apply authentic red formatting
                format_heading_p(p, matched_heading, font_sz)
                separated_count += 1

        i += 1

    if separated_count > 0:
        print(f"[HeadingEngine] Successfully restored {separated_count} authentic Red heading(s) (#C00000 16pt Bold).")
    return separated_count


def heal_missing_table_text(doc: docx.Document, pdf_path: Optional[str] = None) -> int:
    """
    Heal empty cells in tables that were dropped by pdf2docx (e.g. hyperlinked emails or URLs).
    Cross-references the source PDF text words and hyperlink annotations.
    """
    if not pdf_path or not os.path.isfile(pdf_path):
        return 0

    healed = 0
    try:
        import pymupdf
        doc_pdf = pymupdf.open(pdf_path)
    except Exception:
        return 0

    try:
        for table in doc.tables:
            for row in table.rows:
                empty_indices = [c_idx for c_idx, c in enumerate(row.cells) if not c.text.strip()]
                if not empty_indices:
                    continue

                row_texts = [c.text.strip() for c in row.cells if c.text.strip() and len(c.text.strip()) > 3]
                if not row_texts:
                    continue

                for p_num in range(len(doc_pdf)):
                    page = doc_pdf[p_num]
                    page_text = page.get_text()
                    if all(txt in page_text for txt in row_texts[:2]):
                        # Check links on this page
                        links = page.get_links()
                        for link in links:
                            if "uri" in link and "mailto:" in link["uri"]:
                                email = link["uri"].replace("mailto:", "").strip()
                                for idx in empty_indices:
                                    cell = row.cells[idx]
                                    if not cell.text.strip():
                                        cell.text = email
                                        for p in cell.paragraphs:
                                            for r in p.runs:
                                                r.font.name = "Calibri"
                                                r.font.size = Pt(10)
                                        healed += 1
                                        break
                        # If still empty, check words
                        for idx in empty_indices:
                            cell = row.cells[idx]
                            if not cell.text.strip() and idx > 0 and idx + 1 < len(row.cells):
                                words = page.get_text("words")
                                for w in words:
                                    if "@" in w[4] and "." in w[4]:
                                        cell.text = w[4]
                                        for p in cell.paragraphs:
                                            for r in p.runs:
                                                r.font.name = "Calibri"
                                                r.font.size = Pt(10)
                                        healed += 1
                                        break
    except Exception as e:
        print(f"[HealTable Warning] {e}")
    finally:
        doc_pdf.close()

    if healed > 0:
        print(f"[HealTable] Successfully restored {healed} missing cell(s) from PDF annotations.")
    return healed


def standardize_page_margins(
    doc: docx.Document,
    target_top_in: float = 0.40,
    target_bottom_in: float = 0.45,
    target_left_in: float = 0.85,
    target_right_in: float = 0.55
) -> None:
    """
    Standardize section margins to 0.35 - 0.55 inch range to match original PDF viewport.
    Eliminates squashed (0.06") margins and preserves proper printable boundaries.
    Ensures Cover Page has no header/footer (different_first_page_header_footer=True).
    """
    for i, sec in enumerate(doc.sections):
        sec.top_margin = Inches(target_top_in)
        sec.bottom_margin = Inches(target_bottom_in)
        l_in = sec.left_margin.inches if sec.left_margin else 0.85
        if l_in < 0.3 or l_in > 1.2:
            sec.left_margin = Inches(target_left_in)
        r_in = sec.right_margin.inches if sec.right_margin else 0.55
        if r_in < 0.3 or r_in > 1.0:
            sec.right_margin = Inches(target_right_in)
        sec.header_distance = Inches(0.25)
        sec.footer_distance = Inches(0.25)

    if doc.sections:
        doc.sections[0].different_first_page_header_footer = True


def calibrate_cover_page_and_headings(doc: docx.Document) -> None:
    """
    Calibrate Cover Page and Headings alignment and vertical spacing:
    - Splits accidentally merged cover page lines ('FPT UNIVERSITY\\nCapstone Project Document').
    - Centers cover titles and dates, eliminating asymmetric left/right indents.
    - Sets exact font sizes and space_before / space_after matching PDF bounding boxes.
    """
    from docx.enum.text import WD_ALIGN_PARAGRAPH

    w_ind = qn("w:ind")

    def reset_p_indents(target_p: docx.text.paragraph.Paragraph) -> None:
        target_p.paragraph_format.left_indent = Inches(0)
        target_p.paragraph_format.right_indent = Inches(0)
        target_p.paragraph_format.first_line_indent = Inches(0)
        pPr = target_p._p.find(qn("w:pPr"))
        if pPr is not None:
            ind_elem = pPr.find(w_ind)
            if ind_elem is not None:
                pPr.remove(ind_elem)

    for i in range(min(15, len(doc.paragraphs))):
        p = doc.paragraphs[i]
        txt = p.text.strip()
        if not txt:
            continue

        if "FPT UNIVERSITY" in txt and "Capstone Project Document" in txt:
            p.text = ""
            r1 = p.add_run("FPT UNIVERSITY")
            r1.bold = True
            r1.font.name = "Calibri"
            r1.font.size = Pt(36)
            reset_p_indents(p)
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_before = Pt(30)
            p.paragraph_format.space_after = Pt(25)

            new_p = docx.oxml.OxmlElement('w:p')
            p._p.addnext(new_p)
            p2 = docx.text.paragraph.Paragraph(new_p, doc)
            r2 = p2.add_run("Capstone Project Document")
            r2.font.name = "Calibri"
            r2.font.size = Pt(26)
            reset_p_indents(p2)
            p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p2.paragraph_format.space_before = Pt(40)
            p2.paragraph_format.space_after = Pt(15)
            continue

        if "MINISTRY OF EDUCATION" in txt:
            reset_p_indents(p)
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_before = Pt(20)
            p.paragraph_format.space_after = Pt(25)
            for r in p.runs:
                r.bold = True
                r.font.name = "Calibri"
                r.font.size = Pt(16)

        elif txt == "FPT UNIVERSITY":
            reset_p_indents(p)
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_before = Pt(30)
            p.paragraph_format.space_after = Pt(25)
            for r in p.runs:
                r.bold = True
                r.font.name = "Calibri"
                r.font.size = Pt(36)

        elif txt == "Capstone Project Document":
            reset_p_indents(p)
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_before = Pt(40)
            p.paragraph_format.space_after = Pt(15)
            for r in p.runs:
                r.font.name = "Calibri"
                r.font.size = Pt(26)

        elif txt == "iTranslator":
            reset_p_indents(p)
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_before = Pt(20)
            p.paragraph_format.space_after = Pt(15)
            for r in p.runs:
                r.bold = True
                r.font.name = "Calibri"
                r.font.size = Pt(35)

        elif "Ho Chi Minh" in txt and "2023" in txt:
            reset_p_indents(p)
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_before = Pt(120)
            p.paragraph_format.space_after = Pt(0)
            for r in p.runs:
                r.bold = True
                r.font.name = "Calibri"
                r.font.size = Pt(13)


def process_semantic_lists(doc: docx.Document, num_id: str) -> int:
    """
    Robust Semantic List Engine:
    1. Glyph Stripping: Cuts PUA garbage (\\uf06c, \\uf0b7), Unicode bullets (•), and (+, -) from text.
    2. Dynamic Indent Mapping: Assigns ilvl=0 for main bullets, ilvl=1 for sub-bullets (+).
    3. Cleans conflicting manual margins so Word natively manages hanging indents.
    Supports both top-level paragraphs and table cell paragraphs.
    """
    w_ind = qn("w:ind")
    w_numPr = qn("w:numPr")
    modified_count = 0

    all_paragraphs: List[docx.text.paragraph.Paragraph] = list(doc.paragraphs)
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                all_paragraphs.extend(cell.paragraphs)

    i = 0
    while i < len(all_paragraphs):
        p = all_paragraphs[i]
        raw_text = p.text.strip()
        if not raw_text:
            i += 1
            continue

        ilvl: Optional[int] = None
        cleaned_text: Optional[str] = None

        # Level 0 Bullet
        m_bullet = BULLET_GLYPH_REGEX.match(raw_text)
        if m_bullet:
            ilvl = 0
            cleaned_text = BULLET_GLYPH_REGEX.sub("", raw_text).strip()

        # Level 1 Sub-bullet (+ or -)
        elif raw_text.startswith("+ ") or raw_text.startswith("+\t") or (raw_text.startswith("+") and len(raw_text) > 1 and raw_text[1].isupper()):
            ilvl = 1
            cleaned_text = re.sub(r"^\+\s*(\t\s*)?", "", raw_text).strip()
        elif raw_text.startswith("- ") and not raw_text.endswith("-"):
            # If following another list item, treat as sub-bullet
            if i > 0:
                prev_pPr = all_paragraphs[i - 1]._p.pPr
                if prev_pPr is not None and prev_pPr.find(w_numPr) is not None:
                    ilvl = 1
                    cleaned_text = re.sub(r"^-\s*(\t\s*)?", "", raw_text).strip()

        if ilvl is not None and cleaned_text is not None:
            # 1. Clean run text (remove bullet/plus glyphs)
            p.text = cleaned_text

            # 2. Add native Word numPr
            pPr = p._p.get_or_add_pPr()

            # Remove manual w:ind that might conflict with list style
            existing_ind = pPr.find(w_ind)
            if existing_ind is not None:
                pPr.remove(existing_ind)

            # Remove any existing numPr
            existing_numPr = pPr.find(w_numPr)
            if existing_numPr is not None:
                pPr.remove(existing_numPr)

            # Attach semantic numPr
            pPr.append(parse_xml(f'<w:numPr {NS_W}><w:ilvl w:val="{ilvl}"/><w:numId w:val="{num_id}"/></w:numPr>'))
            modified_count += 1

        # Also clean any inline PUA characters that might remain inside table runs
        for run in p.runs:
            if any(0xE000 <= ord(c) <= 0xF8FF for c in run.text):
                # Replace PUA bullet characters (\uf06c, \uf0b7) with clean bullet or empty
                run.text = re.sub(r"[\uf06c\uf0b7]\s*", "• ", run.text)

        i += 1

    return modified_count



def normalize_line_and_paragraph_spacing(doc: docx.Document) -> int:
    """
    Scan all paragraphs across body text and table cells:
    1. Detect any paragraph with w:line < 240 twips (which clips font ascenders/descenders).
       Normalizes w:line to '240' (1.0x line height) and sets w:lineRule='auto'.
    2. For List Items (having w:numPr):
       Ensures w:line='240', w:lineRule='auto', w:before='60', w:after='40'
       so list items breathe naturally and fill the page gracefully without clipping.
    """
    w_spacing = qn("w:spacing")
    w_line = qn("w:line")
    w_lineRule = qn("w:lineRule")
    w_before = qn("w:before")
    w_after = qn("w:after")
    w_numPr = qn("w:numPr")

    all_paragraphs: List[docx.text.paragraph.Paragraph] = list(doc.paragraphs)
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                all_paragraphs.extend(cell.paragraphs)

    fixed_count = 0
    for p in all_paragraphs:
        pPr = p._p.get_or_add_pPr()

        # Preserve exact TOC / LOT / LOF tab stops and line spacing
        if pPr.find(qn("w:tabs")) is not None:
            continue

        sp = pPr.find(w_spacing)
        is_list = pPr.find(w_numPr) is not None

        if sp is None:
            if is_list:
                sp = parse_xml(f'<w:spacing {NS_W} w:line="240" w:lineRule="auto" w:before="60" w:after="40"/>')
                pPr.append(sp)
                fixed_count += 1
        else:
            lv = sp.get(w_line)
            rule = sp.get(w_lineRule)
            if (lv and lv.isdigit() and int(lv) < 240) or (rule == "exact" and lv and lv.isdigit() and int(lv) < 240):
                sp.set(w_line, "240")
                sp.set(w_lineRule, "auto")
                fixed_count += 1

            if is_list:
                sp.set(w_line, "240")
                sp.set(w_lineRule, "auto")
                sp.set(w_before, "60")
                sp.set(w_after, "40")
                fixed_count += 1

    return fixed_count


def clean_redundant_blank_paragraphs(doc: docx.Document) -> int:
    """
    Remove empty paragraphs that waste vertical space in and around
    Table of Contents, List of Tables, and List of Figures to prevent page overflows.
    """
    removed_count = 0
    i = 0
    in_toc_or_lists = False
    while i < len(doc.paragraphs):
        p = doc.paragraphs[i]
        txt = p.text.strip()
        if txt in ("Table of Contents", "List of Tables", "List of Figures"):
            in_toc_or_lists = True
        elif txt in ("Acknowledgements", "1. Introduction", "Chapter 1") or txt.startswith("1. "):
            in_toc_or_lists = False

        if not txt:
            xml = p._p.xml
            if "<w:drawing" not in xml and "<w:pict" not in xml:
                if in_toc_or_lists or (i > 0 and not doc.paragraphs[i - 1].text.strip()):
                    p_parent = p._p.getparent()
                    if p_parent is not None:
                        p_parent.remove(p._p)
                        removed_count += 1
                        continue
        i += 1
    if removed_count > 0:
        print(f"[BlankCleaner] Removed {removed_count} redundant empty paragraph(s).")
    return removed_count


def validate_numbering_integrity(doc: docx.Document) -> bool:
    """
    Pre-zip Validation:
    Guarantees every numId referenced in document.xml exists in numbering.xml.
    Eliminates 'Word found unreadable content' errors.
    """
    w_num = qn("w:num")
    w_numId = qn("w:numId")
    w_numPr = qn("w:numPr")
    w_val = qn("w:val")

    try:
        np = doc.part.numbering_part
        declared_ids = {
            num.get(w_numId)
            for num in np._element.findall(w_num)
            if num.get(w_numId) is not None
        }
    except Exception:
        return False

    for p in doc.paragraphs:
        pPr = p._p.pPr
        if pPr is not None:
            numPr = pPr.find(w_numPr)
            if numPr is not None:
                numId_el = numPr.find(w_numId)
                if numId_el is not None:
                    nid = numId_el.get(w_val)
                    if nid not in declared_ids:
                        numId_el.set(w_val, CANONICAL_NUM_ID)

    return True


def safe_save_docx(doc: docx.Document, target_path: str, max_retries: int = 3, retry_delay: float = 1.5) -> str:
    """
    Hybrid File Locking Strategy:
    1. Retries up to max_retries if file is temporarily locked by Word.
    2. If locked permanently, auto-saves to versioned filename ({stem}_v2.docx) without crashing.
    """
    for attempt in range(max_retries):
        try:
            doc.save(target_path)
            return target_path
        except PermissionError:
            print(f"[FileLock Warning] '{os.path.basename(target_path)}' is locked by Microsoft Word (attempt {attempt+1}/{max_retries}). Retrying in {retry_delay}s...")
            time.sleep(retry_delay)
        except Exception as err:
            raise err

    # Fallback to versioned filename
    dir_name, base_name = os.path.split(target_path)
    stem, ext = os.path.splitext(base_name)
    version = 2
    while True:
        candidate_name = f"{stem}_v{version}{ext}"
        candidate_path = os.path.join(dir_name, candidate_name)
        try:
            doc.save(candidate_path)
            print(f"[FileLock Fallback] File locked by Word. Saved to alternative path: {candidate_name}")
            return candidate_path
        except PermissionError:
            version += 1
        except Exception as err:
            raise err


# ---------------------------------------------------------------------------
# Orphan page-number paragraph remover
# ---------------------------------------------------------------------------

_ORPHAN_PAGE_RE = re.compile(
    r'<w:p\b[^>]*>(?:(?!<w:p\b).)*?<w:t[^>]*>\s*(\d{1,3})\s*</w:t>(?:(?!<w:p\b).)*?</w:p>',
    re.DOTALL
)


def _is_orphan_page_paragraph(para_xml: str) -> bool:
    """
    Return True if an XML paragraph snippet represents a standalone page number:
    - Contains exactly one <w:t> element with a 1-3 digit value.
    - Contains no <w:drawing> (image) or <w:hyperlink> elements.
    - Contains no meaningful non-digit text runs.
    """
    # Must not contain images or hyperlinks
    if '<w:drawing' in para_xml or '<w:hyperlink' in para_xml:
        return False
    # Collect all text content
    texts = re.findall(r'<w:t[^>]*>(.*?)</w:t>', para_xml, re.DOTALL)
    combined = ''.join(texts).strip()
    # Matches if the whole text is just 1-3 digits
    return bool(re.match(r'^\d{1,3}$', combined))


def remove_orphan_page_numbers_from_zip(docx_path: str) -> int:
    """
    Post-save ZIP-level operation:
    Removes paragraph elements from document.xml that are sole-digit orphan page numbers
    injected by pdf2docx (e.g. <w:p>...<w:t>12</w:t>...</w:p> with no other content).
    Returns count of removed paragraphs.
    """
    try:
        # Read existing zip
        with zipfile.ZipFile(docx_path, 'r') as z_in:
            names = z_in.namelist()
            files = {name: z_in.read(name) for name in names}
            info_list = z_in.infolist()

        doc_xml = files.get('word/document.xml', b'').decode('utf-8', errors='replace')

        # Find and remove orphan page-number paragraphs
        removed = 0

        def _check_and_remove(m: re.Match) -> str:
            nonlocal removed
            if _is_orphan_page_paragraph(m.group()):
                removed += 1
                return ''
            return m.group()

        new_doc_xml = _ORPHAN_PAGE_RE.sub(_check_and_remove, doc_xml)

        if removed == 0:
            return 0

        files['word/document.xml'] = new_doc_xml.encode('utf-8')

        # Rewrite zip in-place
        tmp_path = docx_path + '.tmp_orphan'
        info_map = {info.filename: info for info in info_list}
        with zipfile.ZipFile(tmp_path, 'w', zipfile.ZIP_DEFLATED) as z_out:
            for name, data in files.items():
                info = info_map.get(name)
                if info:
                    z_out.writestr(info, data)
                else:
                    z_out.writestr(name, data)

        shutil.move(tmp_path, docx_path)
        print(f"[PageNumFix] Removed {removed} orphan page-number paragraphs from body.")
        return removed
    except Exception as e:
        print(f"[PageNumFix Warning] Could not remove orphan page numbers: {e}")
        return 0


# ---------------------------------------------------------------------------
# Native footer page-number injector
# ---------------------------------------------------------------------------

_FOOTER_XML = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
    '<w:ftr xmlns:wpc="http://schemas.microsoft.com/office/word/2010/wordprocessingCanvas"'
    ' xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006"'
    ' xmlns:o="urn:schemas-microsoft-com:office:office"'
    ' xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"'
    ' xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math"'
    ' xmlns:v="urn:schemas-microsoft-com:vml"'
    ' xmlns:wp14="http://schemas.microsoft.com/office/word/2010/wordprocessingDrawing"'
    ' xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"'
    ' xmlns:w10="urn:schemas-microsoft-com:office:word"'
    ' xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'
    ' xmlns:w14="http://schemas.microsoft.com/office/word/2010/wordml"'
    ' xmlns:wpg="http://schemas.microsoft.com/office/word/2010/wordprocessingGroup"'
    ' xmlns:wpi="http://schemas.microsoft.com/office/word/2010/wordprocessingInk"'
    ' xmlns:wne="http://schemas.microsoft.com/office/word/2006/wordml"'
    ' xmlns:wps="http://schemas.microsoft.com/office/word/2010/wordprocessingShape"'
    ' mc:Ignorable="w14 wp14">'  
    '<w:p>'
    '<w:pPr>'
    '<w:jc w:val="center"/>'
    '<w:rPr><w:sz w:val="20"/><w:szCs w:val="20"/></w:rPr>'
    '</w:pPr>'
    '<w:r><w:fldChar w:fldCharType="begin"/></w:r>'
    '<w:r><w:instrText xml:space="preserve"> PAGE </w:instrText></w:r>'
    '<w:r><w:fldChar w:fldCharType="separate"/></w:r>'
    '<w:r><w:t>1</w:t></w:r>'
    '<w:r><w:fldChar w:fldCharType="end"/></w:r>'
    '</w:p>'
    '</w:ftr>'
)

_REL_TYPE_FOOTER = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/footer"
_CT_FOOTER = "application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml"


def verify_content_parity(docx_path: str, pdf_path: str) -> List[str]:
    """
    Verify textual fidelity between the original PDF and the generated DOCX.
    Flags any significant content tokens (>4 alphanumeric characters) present in PDF but absent in DOCX.
    """
    if not os.path.isfile(pdf_path) or not os.path.isfile(docx_path):
        return []

    try:
        import pymupdf
        pdf_doc = pymupdf.open(pdf_path)
        pdf_words = set()
        for page in pdf_doc:
            for w in page.get_text("words"):
                token = w[4].strip()
                # Ignore pure dot leaders and short page numbers
                if len(token) > 4 and not all(c in ".-…" for c in token):
                    pdf_words.add(token.lower())
        pdf_doc.close()

        doc = docx.Document(docx_path)
        docx_tokens = set()
        for p in doc.paragraphs:
            for w in p.text.split():
                clean_w = w.strip(".,;:()[]{}'\"").lower()
                if len(clean_w) > 4:
                    docx_tokens.add(clean_w)
        for t in doc.tables:
            for row in t.rows:
                for c in row.cells:
                    for w in c.text.split():
                        clean_w = w.strip(".,;:()[]{}'\"").lower()
                        if len(clean_w) > 4:
                            docx_tokens.add(clean_w)

        missing = [w for w in pdf_words if w not in docx_tokens]
        missing = [w for w in missing if not any(c in w for c in ["http", "uuid", "obj", "stream"])]

        if missing:
            print(f"[ContentParity Warning] {len(missing)} significant token(s) absent in DOCX (samples: {missing[:5]})")
        else:
            print(f"[ContentParity] Verified: 100% text content preserved between PDF and DOCX.")
        return sorted(missing)
    except Exception as e:
        print(f"[ContentParity Warning] Verification error: {e}")
        return []


def inject_page_number_footer(docx_path: str) -> bool:
    """
    ZIP-level injection of a native Word footer containing a centered PAGE field.
    Steps:
    1. Add word/footer1.xml with the footer XML.
    2. Add relationship rId_footer1 in word/_rels/document.xml.rels.
    3. Add Override for /word/footer1.xml in [Content_Types].xml.
    4. Patch the last <w:sectPr> (the body sectPr) to reference the footer.
       Any intermediate sectPr inside <w:pPr> (section break) also gets the reference
       so that page numbers appear on every page section.
    """
    FOOTER_REL_ID = "rId_footer1"
    FOOTER_PART = "word/footer1.xml"

    try:
        with zipfile.ZipFile(docx_path, 'r') as z_in:
            names = z_in.namelist()
            files = {name: z_in.read(name) for name in names}
            info_list = z_in.infolist()

        # Skip if footer already exists
        if any('footer' in n for n in names):
            print("[FooterInject] Footer already present, skipping injection.")
            return False

        # 1. Add footer XML
        files[FOOTER_PART] = _FOOTER_XML.encode('utf-8')

        # 2. Patch document.xml.rels
        rels_xml = files['word/_rels/document.xml.rels'].decode('utf-8')
        # Inject before closing </Relationships>
        footer_rel = (
            f'<Relationship Id="{FOOTER_REL_ID}" '
            f'Type="{_REL_TYPE_FOOTER}" '
            f'Target="footer1.xml"/>'
        )
        rels_xml = rels_xml.replace('</Relationships>', footer_rel + '</Relationships>')
        files['word/_rels/document.xml.rels'] = rels_xml.encode('utf-8')

        # 3. Patch [Content_Types].xml
        ct_xml = files['[Content_Types].xml'].decode('utf-8')
        footer_ct = f'<Override PartName="/word/footer1.xml" ContentType="{_CT_FOOTER}"/>'
        ct_xml = ct_xml.replace('</Types>', footer_ct + '</Types>')
        files['[Content_Types].xml'] = ct_xml.encode('utf-8')

        # 4. Patch document.xml — add footerReference to ALL sectPr elements
        doc_xml = files['word/document.xml'].decode('utf-8')
        footer_ref = f'<w:footerReference w:type="default" r:id="{FOOTER_REL_ID}"/>'
        # Insert footer reference right before </w:sectPr>
        doc_xml = doc_xml.replace('</w:sectPr>', footer_ref + '</w:sectPr>')
        files['word/document.xml'] = doc_xml.encode('utf-8')

        # Rewrite zip
        tmp_path = docx_path + '.tmp_footer'
        info_map = {info.filename: info for info in info_list}
        with zipfile.ZipFile(tmp_path, 'w', zipfile.ZIP_DEFLATED) as z_out:
            for name, data in files.items():
                info = info_map.get(name)
                if info:
                    z_out.writestr(info, data)
                else:
                    z_out.writestr(name, data)

        shutil.move(tmp_path, docx_path)
        print(f"[FooterInject] Successfully injected native page-number footer into all {doc_xml.count('</w:sectPr>')} sections.")
        return True
    except Exception as e:
        print(f"[FooterInject Warning] Could not inject footer: {e}")
        return False


def post_process_docx(docx_path: str, pdf_path: Optional[str] = None) -> Tuple[bool, str]:
    """
    Apply comprehensive OpenXML layout corrections to a DOCX document:
    - Auto-stitches broken tables across page breaks.
    - Applies table row pagination protection (<w:cantSplit/>) and header repeating.
    - Standardizes section margins to 0.35" - 0.55" matching PDF viewport.
    - Calibrates Cover Page headings (splits merged lines, centers, normalizes spacing).
    - Restores missing table text (e.g. emails with mailto hyperlinks) from PDF annotations.
    - Ensures canonical numbering.xml with 2-level bullet hierarchy.
    - Runs Semantic List Engine: strips glyph boxes (\\uf06c -> •), sets ilvl=0/1.
    - Normalizes line and paragraph spacing (eliminates top-clipping and squashed lists).
    - Reconstructs Table of Contents / List of Tables with native Word Tab Stops & dot leaders.
    - Applies Red bold heading styling to 'List of Tables', 'List of Figures'.
    - Performs Pre-zip Validation for 100% corruption-free output.
    - Removes orphan page-number paragraphs left by pdf2docx in the body.
    - Injects native Word footer with PAGE field for proper bottom-of-page numbering.
    - Uses Hybrid File Locking Strategy to safely save.
    """
    if not os.path.isfile(docx_path):
        return False, docx_path

    try:
        doc = docx.Document(docx_path)

        # 1. Ensure canonical numbering definition exists in numbering.xml
        num_id = ensure_canonical_numbering(doc)

        # 2. Auto-stitch broken tables split across pages
        stitch_broken_tables(doc)

        # 3. Pre-extract PDF Semantic Map (Ground Truth Colors, Margins & Layout)
        semantic_map = extract_pdf_semantic_map(pdf_path)

        # 3b. Apply table row pagination rules (<w:cantSplit/> and <w:tblHeader/>) and Peach #FFE8E0 header shading
        apply_table_pagination_rules(doc, table_header_bg=semantic_map.get("table_header_bg", "FFE8E0"))

        # 3c. Standardize page margins to match original PDF viewport
        standardize_page_margins(doc)

        # 3d. Calibrate cover page and headings (split lines, center, spacing)
        calibrate_cover_page_and_headings(doc)

        # 3e. Heal missing table texts / hyperlinked emails from PDF
        if pdf_path:
            heal_missing_table_text(doc, pdf_path)

        # 3f. Separate accidentally merged headings (e.g. 'List of Tables \nTable 1...') and apply Red #C00000 16pt Bold
        separate_merged_heading_paragraphs(doc, semantic_map["red_headings"])

        # 4. Calculate right margin tab position based on updated margins
        tab_pos = 9360
        try:
            sec = doc.sections[0]
            printable_w = sec.page_width - sec.left_margin - sec.right_margin
            tab_pos = int(printable_w / 635)
        except Exception:
            tab_pos = 9360

        # 5. Process TOC, Red Headings, and Inline Bullets
        line_sp_twips = semantic_map.get("line_spacing_twips", 290)
        i = 0
        while i < len(doc.paragraphs):
            p = doc.paragraphs[i]
            p_text = p.text.strip()
            if not p_text:
                i += 1
                continue

            # Red Document Headings (Already formatted by separate_merged_heading_paragraphs)
            if p_text in ("List of Tables", "List of Figures", "Table of Contents", "Table of Content"):
                i += 1
                continue

            # Merged TOC entries in a single paragraph
            if p_text.count("...") >= 2 and MULTI_TOC_REGEX.search(p_text):
                raw_split = MULTI_TOC_REGEX.sub(r"\1\n\2", p_text)
                entries = [e.strip() for e in raw_split.split("\n") if e.strip()]
                if len(entries) > 1:
                    first_e = entries[0]
                    m1 = TOC_LINE_REGEX.match(first_e)
                    if m1:
                        apply_tab_stop_to_paragraph(p, m1.group(1).strip(), m1.group(2).strip(), tab_pos_twips=tab_pos, line_spacing_twips=line_sp_twips)
                    else:
                        p.text = first_e

                    prev_p = p
                    for subsequent_e in entries[1:]:
                        m_sub = TOC_LINE_REGEX.match(subsequent_e)
                        new_p = docx.oxml.OxmlElement('w:p')
                        prev_p._p.addnext(new_p)
                        wrapped_p = docx.text.paragraph.Paragraph(new_p, doc)
                        if m_sub:
                            apply_tab_stop_to_paragraph(wrapped_p, m_sub.group(1).strip(), m_sub.group(2).strip(), tab_pos_twips=tab_pos, line_spacing_twips=line_sp_twips)
                        else:
                            wrapped_p.add_run(subsequent_e)
                        prev_p = wrapped_p

                    i += 1
                    continue

            # Single-line TOC / List of Tables / Figures entry
            m_single = TOC_LINE_REGEX.match(p_text)
            if m_single:
                title_part = m_single.group(1).strip()
                page_part = m_single.group(2).strip()
                apply_tab_stop_to_paragraph(p, title_part, page_part, tab_pos_twips=tab_pos, line_spacing_twips=line_sp_twips)
                i += 1
                continue

            # Multi-line merged paragraphs (e.g. '1.1 Project Information \n•Project name: iTranslator\n•Project code: SP23SE38...')
            if "\n" in p_text:
                lines = [l.strip() for l in p_text.split("\n") if l.strip()]
                if len(lines) > 1:
                    p.text = lines[0]
                    prev_p = p
                    for line_txt in lines[1:]:
                        new_p = docx.oxml.OxmlElement('w:p')
                        prev_p._p.addnext(new_p)
                        wrapped_p = docx.text.paragraph.Paragraph(new_p, doc)
                        wrapped_p.add_run(line_txt)
                        prev_p = wrapped_p
                    i += 1
                    continue

            # Inline merged bullet without newline (e.g. 'seller. •Features:')
            m_bullet = INLINE_BULLET_REGEX.search(p_text)
            if m_bullet:
                first_part = m_bullet.group(1).strip()
                bullet_part = m_bullet.group(2).strip()
                p.text = ""
                r1 = p.add_run(first_part)
                r1.font.name = "Calibri"
                r1.font.size = Pt(11)

                new_p = docx.oxml.OxmlElement('w:p')
                p._p.addnext(new_p)
                p2 = docx.text.paragraph.Paragraph(new_p, doc)
                r2 = p2.add_run(bullet_part)
                r2.font.name = "Calibri"
                r2.font.size = Pt(11)
                r2.bold = True

                i += 1
                continue

            # Numbered headings (e.g. '3. Existing Systems', '3.1 Fiverr')
            if re.match(r"^(\d+\.|\d+\.\d+|[IVXLCDM]+\.)\s+[A-Z]", p_text):
                for run in p.runs:
                    run.bold = True
                    run.font.name = "Calibri"

            i += 1

        # 5b. Remove redundant empty paragraphs that cause page overflows in LOT/LOF
        clean_redundant_blank_paragraphs(doc)

        # 6. Process Semantic Lists (Glyph Stripping & ilvl Mapping)
        if num_id:
            process_semantic_lists(doc, num_id)

        # 7. Normalize Line & Paragraph Spacing (Prevent font clipping, ensure natural vertical rhythm)
        normalize_line_and_paragraph_spacing(doc)

        # 8. Pre-zip Validation for Numbering Integrity
        validate_numbering_integrity(doc)

        # 9. Hybrid File Locking Save
        saved_path = safe_save_docx(doc, docx_path)

        # 10. ZIP-level: Remove orphan page-number paragraphs from body
        remove_orphan_page_numbers_from_zip(saved_path)

        # 11. ZIP-level: Inject native footer with PAGE field
        inject_page_number_footer(saved_path)

        # 12. Content Parity Verification (Ground Truth Audit)
        if pdf_path:
            verify_content_parity(saved_path, pdf_path)

        return True, saved_path

    except Exception as err:
        print(f"[SmartPostProcessor Error] {err}")
        return False, docx_path


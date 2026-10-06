import os
import sys

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
import docx
from PIL import Image
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import qn, nsdecls

DOCX_PATH = r"tool/AI-Docx-Testing-Product/Report3_Software Requirement Specification.docx"
PNG_PATH = r"tool/AI-Docx-Testing-Product/android_user_screen_flow.png"

def update_docx():
    print(f"Loading DOCX: {DOCX_PATH}")
    doc = docx.Document(DOCX_PATH)

    # ─────────────────────────────────────────────────────────────
    # 1. Update image in Paragraph 71 (3.1.2 Android User Screen Flow)
    # ─────────────────────────────────────────────────────────────
    p71 = doc.paragraphs[71]
    drawings = p71._element.xpath('.//w:drawing')
    if not drawings:
        raise ValueError("No drawing found in P71!")

    blips = p71._element.xpath('.//a:blip')
    if not blips:
        raise ValueError("No blip found in P71 drawing!")

    embed_rId = blips[0].attrib.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed')
    print(f"Found blip rId: {embed_rId}")

    # Read new image binary and measure dimensions
    with open(PNG_PATH, "rb") as f:
        new_png_data = f.read()

    with Image.open(PNG_PATH) as img:
        png_w_px, png_h_px = img.size

    w_cm = 14.0
    h_cm = round((png_h_px / png_w_px) * w_cm, 2)
    cx_emu = int(w_cm * 360000)
    cy_emu = int(h_cm * 360000)

    rel = doc.part.rels[embed_rId]
    rel.target_part._blob = new_png_data
    print(f"Replaced image blob for {rel.target_ref} ({len(new_png_data)} bytes)")
    print(f"Image dimensions: {png_w_px}x{png_h_px}px -> {w_cm}cm x {h_cm}cm ({cx_emu} x {cy_emu} EMUs)")

    for extent in p71._element.xpath('.//wp:extent'):
        extent.set('cx', str(cx_emu))
        extent.set('cy', str(cy_emu))

    for a_ext in p71._element.xpath('.//a:xfrm/a:ext'):
        a_ext.set('cx', str(cx_emu))
        a_ext.set('cy', str(cy_emu))

    # Keep headings with next element
    for p_idx in [66, 67, 68, 70, 73, 74]:
        if p_idx < len(doc.paragraphs):
            pPr = doc.paragraphs[p_idx]._element.get_or_add_pPr()
            if pPr.find(qn("w:keepNext")) is None:
                pPr.append(OxmlElement("w:keepNext"))

    # Force pageBreakBefore on P73 ("3.1.2 Screen Descriptions")
    # This cleanly moves Table 1 to start at the top of Page 10, keeping all 18 rows together
    p73_pPr = doc.paragraphs[73]._element.get_or_add_pPr()
    if p73_pPr.find(qn("w:pageBreakBefore")) is None:
        p73_pPr.append(OxmlElement("w:pageBreakBefore"))

    # Remove empty paragraph P75 if it exists and is empty
    if len(doc.paragraphs) > 75 and doc.paragraphs[75].text.strip() == "":
        p75_elem = doc.paragraphs[75]._element
        p75_elem.getparent().remove(p75_elem)
        print("Removed empty paragraph between Table 1 heading and Table 1.")

    # ─────────────────────────────────────────────────────────────
    # 2. Format ALL tables in the document:
    #    - cantSplit on every row (prevents row splitting across pages)
    #    - tblHeader on row 0 (repeats header on new pages)
    #    - vAlign="center" on every cell
    # ─────────────────────────────────────────────────────────────
    print(f"Formatting all {len(doc.tables)} tables with cantSplit, tblHeader, and vAlign center...")
    for t_idx, table in enumerate(doc.tables):
        if not table.rows:
            continue

        # Header row configuration
        header_trPr = table.rows[0]._tr.get_or_add_trPr()
        if header_trPr.find(qn('w:tblHeader')) is None:
            header_trPr.append(parse_xml(r'<w:tblHeader %s/>' % nsdecls('w')))

        # Apply cantSplit and vAlign to all rows & cells
        for row in table.rows:
            trPr = row._tr.get_or_add_trPr()
            if trPr.find(qn('w:cantSplit')) is None:
                trPr.append(parse_xml(r'<w:cantSplit %s/>' % nsdecls('w')))

            for cell in row.cells:
                cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
                tcPr = cell._tc.get_or_add_tcPr()
                valign = tcPr.find(qn('w:vAlign'))
                if valign is not None:
                    valign.set(qn('w:val'), 'center')
                else:
                    tcPr.append(parse_xml(r'<w:vAlign %s w:val="center"/>' % nsdecls('w')))

    # ─────────────────────────────────────────────────────────────
    # 3. Specifically format Table 1 (Robot Screen Flow, doc.tables[3])
    #    Standardize font to Calibri 10pt (matching Table 2) so all 18 rows fit cleanly on Page 10
    #    Ensure clean column text alignments (col 0: Center, cols 1-3: Left)
    # ─────────────────────────────────────────────────────────────
    t1 = doc.tables[3]
    print(f"Formatting Table 1 ({len(t1.rows)} rows)...")
    for row_idx, row in enumerate(t1.rows):
        for col_idx, cell in enumerate(row.cells):
            for p in cell.paragraphs:
                if col_idx == 0:
                    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                else:
                    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                for r in p.runs:
                    r.font.name = "Calibri"
                    if row_idx == 0:
                        r.font.size = Pt(10)
                        r.font.bold = True
                    else:
                        r.font.size = Pt(10)

    # ─────────────────────────────────────────────────────────────
    # 4. Specifically format Table 2 (Android User Screen Flow, doc.tables[4])
    # ─────────────────────────────────────────────────────────────
    t2 = doc.tables[4]
    print(f"Formatting Table 2 ({len(t2.rows)} rows)...")
    for row_idx, row in enumerate(t2.rows):
        for col_idx, cell in enumerate(row.cells):
            for p in cell.paragraphs:
                if col_idx == 0:
                    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                else:
                    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                for r in p.runs:
                    r.font.name = "Calibri"
                    if row_idx == 0:
                        r.font.size = Pt(10)
                        r.font.bold = True
                    else:
                        r.font.size = Pt(10)

    # ─────────────────────────────────────────────────────────────
    # 5. Save document safely
    # ─────────────────────────────────────────────────────────────
    doc.save(DOCX_PATH)
    print(f"[OK] Successfully saved updated document to {DOCX_PATH}")

if __name__ == "__main__":
    update_docx()

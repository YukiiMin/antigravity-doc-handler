import os
import sys
import docx
from PIL import Image

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DOCX_PATH = r"E:\Do_an_SU26\SuperMarketBot-BE\docs\Report4_Software Design Document.docx"
PNG_PATH = os.path.join(ROOT_DIR, "diagram_assets", "master_erd_smart_mart.png")

def patch_master_erd():
    print(f"Loading DOCX: {DOCX_PATH}")
    doc = docx.Document(DOCX_PATH)

    p53 = doc.paragraphs[53]
    drawings = p53._element.xpath('.//w:drawing')
    if not drawings:
        raise ValueError("No drawing found in Paragraph 53!")

    blips = p53._element.xpath('.//a:blip')
    if not blips:
        raise ValueError("No blip found in P53 drawing!")

    embed_rId = blips[0].attrib.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed')
    print(f"Found blip rId: {embed_rId}")

    # Read new image binary and measure dimensions
    with open(PNG_PATH, "rb") as f:
        new_png_data = f.read()

    with Image.open(PNG_PATH) as img:
        png_w_px, png_h_px = img.size

    w_cm = 16.51
    h_cm = round((png_h_px / png_w_px) * w_cm, 2)
    cx_emu = int(w_cm * 360000)
    cy_emu = int(h_cm * 360000)

    rel = doc.part.rels[embed_rId]
    rel.target_part._blob = new_png_data
    print(f"Replaced image blob for {rel.target_ref} ({len(new_png_data)} bytes)")
    print(f"Image dimensions: {png_w_px}x{png_h_px}px -> {w_cm}cm x {h_cm}cm ({cx_emu} x {cy_emu} EMUs)")

    for extent in p53._element.xpath('.//wp:extent'):
        extent.set('cx', str(cx_emu))
        extent.set('cy', str(cy_emu))

    for a_ext in p53._element.xpath('.//a:xfrm/a:ext'):
        a_ext.set('cx', str(cx_emu))
        a_ext.set('cy', str(cy_emu))

    doc.save(DOCX_PATH)
    print(f"[OK] Successfully saved updated document to: {DOCX_PATH}")

if __name__ == "__main__":
    patch_master_erd()

import os
import shutil
import sys
import docx
from PIL import Image
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

DOCX_PATH = r"../AI-Docx-Testing-Product/Report3_Software Requirement Specification.docx"
BAK_PATH = r"../AI-Docx-Testing-Product/Report3_Software Requirement Specification.docx.bak_v4"

USER_PNG_PATH = r"../AI-Docx-Testing-Product/android_user_screen_flow_v2.png"
STAFF_PNG_PATH = r"../AI-Docx-Testing-Product/android_staff_screen_flow.png"

def update_docx():
    print(f"1. Creating backup: {BAK_PATH}")
    shutil.copyfile(DOCX_PATH, BAK_PATH)
    print("   Backup created successfully.")

    print(f"2. Loading DOCX: {DOCX_PATH}")
    doc = docx.Document(DOCX_PATH)

    w_cm = 14.0

    # ─────────────────────────────────────────────────────────────
    # Step A: Update User Screen Flow diagram in Paragraph 71
    # ─────────────────────────────────────────────────────────────
    p71 = doc.paragraphs[71]
    blips = p71._element.xpath('.//a:blip')
    if not blips:
        raise ValueError("No blip found in P71 drawing!")
    u_rId = blips[0].attrib.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed')

    with open(USER_PNG_PATH, "rb") as f:
        new_user_png_data = f.read()

    with Image.open(USER_PNG_PATH) as img:
        u_w_px, u_h_px = img.size

    u_h_cm = round((u_h_px / u_w_px) * w_cm, 2)
    u_cx_emu = int(w_cm * 360000)
    u_cy_emu = int(u_h_cm * 360000)

    u_rel = doc.part.rels[u_rId]
    u_rel.target_part._blob = new_user_png_data
    print(f"   Replaced User diagram blob for {u_rel.target_ref} ({len(new_user_png_data)} bytes)")
    print(f"   User Diagram: {u_w_px}x{u_h_px}px -> {w_cm}cm x {u_h_cm}cm ({u_cx_emu} x {u_cy_emu} EMUs)")

    for extent in p71._element.xpath('.//wp:extent'):
        extent.set('cx', str(u_cx_emu))
        extent.set('cy', str(u_cy_emu))

    for a_ext in p71._element.xpath('.//a:xfrm/a:ext'):
        a_ext.set('cx', str(u_cx_emu))
        a_ext.set('cy', str(u_cy_emu))

    # ─────────────────────────────────────────────────────────────
    # Step B: Update Staff Screen Flow diagram in Paragraph 74
    # ─────────────────────────────────────────────────────────────
    p74 = doc.paragraphs[74]
    blips_staff = p74._element.xpath('.//a:blip')
    if not blips_staff:
        raise ValueError("No blip found in P74 drawing!")
    s_rId = blips_staff[0].attrib.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed')

    with open(STAFF_PNG_PATH, "rb") as f:
        new_staff_png_data = f.read()

    with Image.open(STAFF_PNG_PATH) as img:
        s_w_px, s_h_px = img.size

    s_h_cm = round((s_h_px / s_w_px) * w_cm, 2)
    s_cx_emu = int(w_cm * 360000)
    s_cy_emu = int(s_h_cm * 360000)

    s_rel = doc.part.rels[s_rId]
    s_rel.target_part._blob = new_staff_png_data
    print(f"   Replaced Staff diagram blob for {s_rel.target_ref} ({len(new_staff_png_data)} bytes)")
    print(f"   Staff Diagram: {s_w_px}x{s_h_px}px -> {w_cm}cm x {s_h_cm}cm ({s_cx_emu} x {u_cy_emu} EMUs)")

    for extent in p74._element.xpath('.//wp:extent'):
        extent.set('cx', str(s_cx_emu))
        extent.set('cy', str(s_cy_emu))

    for a_ext in p74._element.xpath('.//a:xfrm/a:ext'):
        a_ext.set('cx', str(s_cx_emu))
        a_ext.set('cy', str(s_cy_emu))

    # ─────────────────────────────────────────────────────────────
    # Step C: Update Table 5 Screen Column with Standardized English
    # ─────────────────────────────────────────────────────────────
    print("3. Updating Table 5 (Staff Screen Descriptions) to standardized English screen names...")
    t5 = doc.tables[5]
    screen_names = [
        "Staff Login Screen",
        "Staff Home Dashboard",
        "Notifications Tab (Empty Shelves)",
        "Task Detail & Restock Screen",
        "Shelf Density Section (Shelves 1..6)",
        "In-Place Shelf Fill Modal",
        "Robot RB0001 Telemetry",
        "Interactive Map Tab 2D",
        "Profile Tab",
        "SignalR Restock Sync (100% Broadcast)"
    ]

    for idx, name in enumerate(screen_names):
        row = t5.rows[idx + 1]
        cell = row.cells[2] # Screen column
        cell.text = ""
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(0)
        r = p.add_run(name)
        r.font.name = "Calibri"
        r.font.size = Pt(9.5)
        r.font.bold = True
        r.font.color.rgb = RGBColor(0x00, 0x00, 0x00)

    # Save document
    print(f"4. Saving updated document to: {DOCX_PATH}")
    doc.save(DOCX_PATH)
    print("   Document saved successfully!")

if __name__ == "__main__":
    update_docx()
